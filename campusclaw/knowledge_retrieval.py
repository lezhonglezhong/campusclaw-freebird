"""Class-scoped chunk retrieval and public provenance formatting."""

from __future__ import annotations

from dataclasses import dataclass
import math
import unicodedata
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from campusclaw.models import KnowledgeChunk, Material
from campusclaw.ai_providers import EmbeddingProvider, ProviderUnavailable
from campusclaw.vector_store import VectorStore


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
    titles = {
        material.id: unicodedata.normalize("NFKC", material.display_name).strip().casefold()
        for material in session.query(Material).filter_by(class_id=class_id).all()
    }
    scored = []
    needle = unicodedata.normalize("NFKC", query).casefold()
    for chunk in candidates:
        literal_count = chunk.chunk_text.casefold().count(needle)
        fulltext_score = fts_scores.get(chunk.id, 0.0)
        title = titles.get(chunk.material_id, "")
        title_match = len(title) >= 3 and title in needle
        if literal_count or fulltext_score or title_match:
            scored.append((chunk, float(literal_count) + fulltext_score + (2.0 if title_match else 0.0)))
    scored.sort(key=lambda item: (-item[1], item[0].id))
    return [RankedChunk(chunk=chunk, keyword_score=score, keyword_rank=index)
            for index, (chunk, score) in enumerate(scored[:limit], start=1)]


def vector_retrieve(
    session: Session, query: str, class_id: int, embedding: EmbeddingProvider,
    store: VectorStore, limit: int = 20,
) -> list[RankedChunk]:
    """Filter cosine candidates, then hydrate text using a fresh class check."""
    try:
        vector = embedding.embed([query])[0]
        points = store.search(vector, class_id, limit)
    except (IndexError, TypeError, ValueError) as exc:
        raise ProviderUnavailable("vector_unavailable") from exc
    ranked: list[tuple[KnowledgeChunk, float]] = []
    seen: set[int] = set()
    for point in points:
        if not isinstance(point, dict):
            continue
        point_id, score = point.get("id"), point.get("score")
        if (
            isinstance(point_id, bool) or not isinstance(point_id, int)
            or isinstance(score, bool) or not isinstance(score, (int, float))
            or not math.isfinite(score) or score < 0.35 or point_id in seen
        ):
            continue
        seen.add(point_id)
        chunk = session.query(KnowledgeChunk).filter_by(
            id=point_id, class_id=class_id, vector_status="ready",
            text_status="ready",
        ).one_or_none()
        if chunk is not None:
            ranked.append((chunk, float(score)))
    ranked.sort(key=lambda item: (-item[1], item[0].id))
    return [RankedChunk(chunk=chunk, vector_score=score, vector_rank=index)
            for index, (chunk, score) in enumerate(ranked[:limit], start=1)]


def hybrid_retrieve(
    session: Session, query: str, class_id: int, embedding: EmbeddingProvider,
    store: VectorStore, limit: int = 20,
) -> list[RankedChunk]:
    """Fuse already filtered keyword and vector ranks with RRF k=60."""
    keyword = keyword_retrieve(session, query, class_id, limit)
    vector = vector_retrieve(session, query, class_id, embedding, store, limit)
    by_id: dict[int, RankedChunk] = {}
    for source in (keyword, vector):
        for hit in source:
            combined = by_id.get(hit.chunk.id)
            if combined is None:
                combined = RankedChunk(chunk=hit.chunk, rrf_score=0.0)
                by_id[hit.chunk.id] = combined
            if hit.keyword_rank is not None:
                combined.keyword_rank = hit.keyword_rank
                combined.keyword_score = hit.keyword_score
                combined.rrf_score += 1.0 / (60 + hit.keyword_rank)
            if hit.vector_rank is not None:
                combined.vector_rank = hit.vector_rank
                combined.vector_score = hit.vector_score
                combined.rrf_score += 1.0 / (60 + hit.vector_rank)
    ranked = sorted(
        by_id.values(),
        key=lambda hit: (
            -hit.rrf_score,
            min(rank for rank in (hit.keyword_rank, hit.vector_rank) if rank is not None),
            hit.chunk.id,
        ),
    )
    return ranked[:limit]


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

