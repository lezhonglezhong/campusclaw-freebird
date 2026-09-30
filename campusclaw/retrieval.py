"""SQLite FTS5 index helpers for material-content retrieval."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from campusclaw.models import Material


def initialize_retrieval_index(session: Session) -> None:
    if session.get_bind().dialect.name != "sqlite":
        return
    session.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS material_retrieval
        USING fts5(material_id UNINDEXED, class_id UNINDEXED, content)
    """))


def index_material(session: Session, material: Material, content: str) -> None:
    session.execute(text("DELETE FROM material_retrieval WHERE material_id = :material_id"), {"material_id": material.id})
    session.execute(
        text("INSERT INTO material_retrieval(material_id, class_id, content) VALUES (:material_id, :class_id, :content)"),
        {"material_id": material.id, "class_id": material.class_id, "content": content},
    )


def remove_material_from_index(session: Session, material_id: int) -> None:
    session.execute(text("DELETE FROM material_retrieval WHERE material_id = :material_id"), {"material_id": material_id})
