"""Relational source-first indexing, independent of vector availability."""

from sqlalchemy.orm import Session

from campusclaw.ai_providers import EmbeddingProvider, ProviderUnavailable
from campusclaw.chunking import chunk_text
from campusclaw.models import KnowledgeChunk, KnowledgeEntry, Material
from campusclaw.vector_store import VectorStore


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


def vectorize_entry(
    session: Session, entry: KnowledgeEntry, embedding: EmbeddingProvider, store: VectorStore
) -> None:
    """Index one point per chunk; a failed chunk never receives a new point."""
    session.flush()
    chunks = list(entry.chunks)
    if not chunks:
        entry.vector_status = "failed"
        return
    try:
        store.ensure_collection()
    except ProviderUnavailable:
        for chunk in chunks:
            chunk.vector_status = "failed"
        entry.vector_status = "failed"
        return
    failed = False
    for chunk in chunks:
        try:
            vector = embedding.embed([chunk.chunk_text])[0]
            store.upsert([{
                "id": chunk.id,
                "vector": vector,
                "payload": {
                    "class_id": chunk.class_id,
                    "material_id": chunk.material_id,
                    "knowledge_entry_id": entry.id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                },
            }])
        except (ProviderUnavailable, IndexError, TypeError, ValueError):
            chunk.vector_status = "failed"
            failed = True
        else:
            chunk.vector_status = "ready"
    entry.vector_status = "failed" if failed else "ready"
