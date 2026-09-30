"""One-time, non-destructive import of the prior SQLite application data."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3

from flask import Flask

from campusclaw.models import Class, Material, User


def migrate_legacy_sqlite(app: Flask, source: Path | None = None) -> int:
    """Copy old identities and materials into an empty MySQL database."""
    session = app.extensions["sqlalchemy"]["session"]
    if session.get_bind().dialect.name != "mysql":
        raise RuntimeError("legacy migration requires a MySQL target")
    if session.query(Class).count() or session.query(User).count() or session.query(Material).count():
        raise RuntimeError("migration target must be empty")
    source = source or Path(app.instance_path) / "campusclaw.sqlite3"
    if not source.is_file():
        raise RuntimeError("legacy SQLite source is missing")
    with sqlite3.connect(source) as old:
        old.row_factory = sqlite3.Row
        classes = old.execute("SELECT id, name FROM classes ORDER BY id").fetchall()
        users = old.execute(
            "SELECT id, account, password_hash, role, class_id FROM users ORDER BY id"
        ).fetchall()
        materials = old.execute(
            "SELECT id, display_name, class_id, uploader_id, content_path, status, created_at "
            "FROM materials ORDER BY id"
        ).fetchall()
    source_root = source.parent.resolve()
    translated_paths = {
        row["id"]: source_root / "materials" / Path(row["content_path"]).name
        for row in materials
    }
    missing = [row["id"] for row in materials if not translated_paths[row["id"]].is_file()]
    if missing:
        raise RuntimeError("legacy material source files are missing")
    try:
        session.add_all(Class(id=row["id"], name=row["name"]) for row in classes)
        session.flush()
        session.add_all(User(
            id=row["id"], account=row["account"], password_hash=row["password_hash"],
            role=row["role"], class_id=row["class_id"],
        ) for row in users)
        session.flush()
        session.add_all(Material(
            id=row["id"], display_name=row["display_name"], class_id=row["class_id"],
            uploader_id=row["uploader_id"], content_path=str(translated_paths[row["id"]]),
            status=row["status"], created_at=datetime.fromisoformat(row["created_at"]),
        ) for row in materials)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return len(materials)

