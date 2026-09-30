"""Repeatable local development data."""

from pathlib import Path

from flask import Flask
from werkzeug.security import generate_password_hash

from campusclaw.models import Class, Material, User
from campusclaw.retrieval import index_material
from campusclaw.knowledge_indexing import ensure_material_knowledge


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
        ensure_material_knowledge(session, material, seed_content)
    session.commit()


def register_seed_command(app: Flask) -> None:
    """Expose seeding as ``flask --app campusclaw seed``."""

    @app.cli.command("seed")
    def seed_command() -> None:
        seed_data(app)
