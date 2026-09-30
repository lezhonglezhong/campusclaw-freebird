"""Repeatable local development data."""

from pathlib import Path

from flask import Flask
import click
from werkzeug.security import generate_password_hash

from campusclaw.models import Class, Material, User
from campusclaw.retrieval import index_material
from campusclaw.knowledge_indexing import ensure_material_knowledge, refresh_keyword_index
from campusclaw.knowledge_indexing import vectorize_entry
from campusclaw.models import KnowledgeEntry


SEED_ACCOUNTS = {
    "teacher-a": {"password": "teacher-a-password", "role": "teacher", "class_name": "A"},
    "student-a": {"password": "student-a-password", "role": "student", "class_name": "A"},
    "teacher-b": {"password": "teacher-b-password", "role": "teacher", "class_name": "B"},
    "student-b": {"password": "student-b-password", "role": "student", "class_name": "B"},
}


def seed_data(app: Flask) -> None:
    """Create the fixed local sample data without duplicating existing rows."""
    session = app.extensions["sqlalchemy"]["session"]
    storage_dir = Path(app.config["MATERIAL_STORAGE_DIR"])
    storage_dir.mkdir(parents=True, exist_ok=True)
    classes = {}
    for name in ("A", "B"):
        class_ = session.query(Class).filter_by(name=name).one_or_none()
        if class_ is None:
            class_ = Class(name=name)
            session.add(class_)
        classes[name] = class_
    session.flush()

    for account, details in SEED_ACCOUNTS.items():
        if session.query(User).filter_by(account=account).one_or_none() is None:
            session.add(
                User(
                    account=account,
                    password_hash=generate_password_hash(details["password"]),
                    role=details["role"],
                    class_=classes[details["class_name"]],
                )
            )
    session.flush()

    for class_name in ("A", "B"):
        class_ = classes[class_name]
        teacher = session.query(User).filter_by(account=f"teacher-{class_name.lower()}").one()
        display_name = f"Class {class_name} sample material"
        seed_path = storage_dir / f"seed-class-{class_name.lower()}.txt"
        seed_content = f"Class {class_name} sample material content.\n"
        seed_path.write_text(seed_content, encoding="utf-8")
        material = session.query(Material).filter_by(class_id=class_.id, display_name=display_name).one_or_none()
        if material is None:
            material = Material(
                display_name=display_name,
                class_=class_,
                uploader=teacher,
                content_path=str(seed_path),
                status="ready",
            )
            session.add(material)
        else:
            material.uploader = teacher
            material.content_path = str(seed_path)
        session.flush()
        index_material(session, material, seed_content)
        entry = ensure_material_knowledge(session, material, seed_content)
        refresh_keyword_index(session, entry)
        if entry.vector_status == "pending":
            vectorize_entry(session, entry, app.extensions["embedding_provider"], app.extensions["vector_store"])
    session.commit()


def backfill_knowledge(app: Flask) -> int:
    """Create missing relational chunk sets for existing UTF-8 materials."""
    session = app.extensions["sqlalchemy"]["session"]
    count = 0
    for material in session.query(Material).order_by(Material.id):
        if session.query(KnowledgeEntry).filter_by(material_id=material.id).first() is not None:
            continue
        try:
            body = Path(material.content_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if not body:
            continue
        entry = ensure_material_knowledge(session, material, body)
        refresh_keyword_index(session, entry)
        vectorize_entry(session, entry, app.extensions["embedding_provider"], app.extensions["vector_store"])
        count += 1
    session.commit()
    return count


def register_seed_command(app: Flask) -> None:
    """Expose seeding as ``flask --app campusclaw seed``."""

    @app.cli.command("seed")
    def seed_command() -> None:
        seed_data(app)

    @app.cli.command("backfill-knowledge")
    def backfill_command() -> None:
        backfill_knowledge(app)

    @app.cli.command("migrate-legacy-sqlite")
    @click.option("--source", type=click.Path(path_type=Path), default=None)
    def migrate_command(source: Path | None) -> None:
        from campusclaw.migration import migrate_legacy_sqlite
        migrate_legacy_sqlite(app, source)
