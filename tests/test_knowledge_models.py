from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from campusclaw import create_app
from campusclaw.models import Class, KnowledgeChunk, KnowledgeEntry, Material, User


def test_entry_and_chunks_are_class_scoped_and_unique(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'knowledge.sqlite3'}", "TOKEN_SIGNING_SECRET": "secret"})
    session = app.extensions["sqlalchemy"]["session"]
    classroom = Class(name="A")
    user = User(account="teacher", password_hash="hash", role="teacher", class_=classroom)
    material = Material(display_name="notes", class_=classroom, uploader=user, content_path="/tmp/a", status="ready")
    entry = KnowledgeEntry(material=material, class_=classroom, body_text="original")
    session.add_all([classroom, user, material, entry])
    session.flush()
    session.add(KnowledgeChunk(entry=entry, material_id=material.id, class_id=classroom.id, chunk_index=0, start_offset=0, end_offset=8, chunk_text="original"))
    session.commit()
    assert session.query(KnowledgeChunk).one().vector_status == "pending"
    with pytest.raises(IntegrityError):
        session.add(KnowledgeChunk(entry=entry, material_id=material.id, class_id=classroom.id, chunk_index=0, start_offset=0, end_offset=1, chunk_text="x"))
        session.commit()
