"""Class-scoped chunk retrieval and public provenance formatting."""

from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.orm import Session

from campusclaw.models import KnowledgeChunk, Material


@dataclass
class RankedChunk:
    chunk: KnowledgeChunk
    keyword_score: float | None = None
    keyword_rank: int | None = None
    vector_score: float | None = None
    vector_rank: int | None = None
    rrf_score: float | None = None


def keyword_retrieve(session: Session, query: str, class_id: int, limit: int = 20) -> list[RankedChunk]:
    """Use the relational text index, with literal matching for CJK phrases."""
    fts_scores: dict[int, float] = {}
    if session.get_bind().dialect.name == "sqlite":
        try:
            quoted = '"' + query.replace('"', '""') + '"'
            rows = session.execute(text(
                "SELECT chunk_id, bm25(knowledge_chunk_retrieval) "
                "FROM knowledge_chunk_retrieval "
                "WHERE knowledge_chunk_retrieval MATCH :query AND class_id = :class_id "
                "ORDER BY bm25(knowledge_chunk_retrieval) LIMIT :limit"
            ), {"query": quoted, "class_id": class_id, "limit": limit}).all()
            fts_scores = {int(row[0]): max(0.0, -float(row[1])) for row in rows}
        except Exception:
            fts_scores = {}
    elif session.get_bind().dialect.name == "mysql":
        rows = session.execute(text(
            "SELECT id, MATCH(chunk_text) AGAINST (:query IN NATURAL LANGUAGE MODE) AS score "
            "FROM knowledge_chunks WHERE class_id = :class_id AND text_status = 'ready' "
            "AND MATCH(chunk_text) AGAINST (:query IN NATURAL LANGUAGE MODE) > 0 "
            "ORDER BY score DESC LIMIT :limit"
        ), {"query": query, "class_id": class_id, "limit": limit}).all()
        fts_scores = {int(row[0]): float(row[1]) for row in rows}
    candidates = session.query(KnowledgeChunk).filter_by(
        class_id=class_id, text_status="ready"
    ).all()
    scored = []
    needle = query.casefold()
    for chunk in candidates:
        literal_count = chunk.chunk_text.casefold().count(needle)
        fulltext_score = fts_scores.get(chunk.id, 0.0)
        if literal_count or fulltext_score:
            scored.append((chunk, float(literal_count) + fulltext_score))
    scored.sort(key=lambda item: (-item[1], item[0].id))
    return [RankedChunk(chunk=chunk, keyword_score=score, keyword_rank=index)
            for index, (chunk, score) in enumerate(scored[:limit], start=1)]


def public_hit(session: Session, hit: RankedChunk) -> dict:
    """Format only authorized relational provenance for an API response."""
    material = session.query(Material).filter_by(id=hit.chunk.material_id, class_id=hit.chunk.class_id).one()
    result = {
        "chunk_id": hit.chunk.id,
        "material_id": material.id,
        "material_title": material.display_name,
        "chunk_index": hit.chunk.chunk_index,
        "start_offset": hit.chunk.start_offset,
        "end_offset": hit.chunk.end_offset,
        "excerpt": hit.chunk.chunk_text[:240],
        "material_url": f"/api/materials/{material.id}",
    }
    for field in ("keyword_score", "keyword_rank", "vector_score", "vector_rank", "rrf_score"):
        value = getattr(hit, field)
        if value is not None:
            result[field] = value
    return result

