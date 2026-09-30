"""Relational source-first indexing, independent of vector availability."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from campusclaw.chunking import chunk_text
from campusclaw.models import KnowledgeChunk, KnowledgeEntry, Material


def ensure_material_knowledge(session: Session, material: Material, body: str) -> KnowledgeEntry:
    entry = session.query(KnowledgeEntry).filter_by(material_id=material.id).one_or_none()
    if entry is not None:
        return entry
    entry = KnowledgeEntry(material_id=material.id, class_id=material.class_id, body_text=body, strategy="auto", text_status="ready", vector_status="pending")
    session.add(entry)
    session.flush()
    for chunk in chunk_text(body):
        session.add(KnowledgeChunk(knowledge_entry_id=entry.id, material_id=material.id, class_id=material.class_id, chunk_index=chunk.index, start_offset=chunk.start_offset, end_offset=chunk.end_offset, chunk_text=chunk.text, text_status="ready", vector_status="pending"))
    return entry
