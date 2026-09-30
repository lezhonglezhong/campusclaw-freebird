"""Identifier-only vector-store contract and Qdrant HTTP adapter."""

from __future__ import annotations

from typing import Any, Protocol

from campusclaw.ai_providers import ProviderUnavailable, Transport, _post_json
from campusclaw.runtime_config import GatewaySettings


class VectorStore(Protocol):
    def ensure_collection(self) -> None: ...
    def upsert(self, points: list[dict[str, Any]]) -> None: ...
    def delete(self, point_ids: list[int]) -> None: ...
    def search(self, vector: list[float], class_id: int, limit: int) -> list[dict[str, Any]]: ...


class QdrantVectorStore:
    collection_name = "campusclaw_chunks"

    def __init__(self, settings: GatewaySettings, transport: Transport = _post_json) -> None:
        self.settings, self.transport = settings, transport

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.qdrant_url:
            raise ProviderUnavailable("vector_store_unavailable")
        # Qdrant is normally internal and unauthenticated in this course compose stack.
        return self.transport(f"{self.settings.qdrant_url}{path}", payload, "", self.settings.timeout_seconds)

    def ensure_collection(self) -> None:
        self._request(f"/collections/{self.collection_name}", {
            "vectors": {"size": self.settings.embedding_dim, "distance": "Cosine"},
        })

    def upsert(self, points: list[dict[str, Any]]) -> None:
        for point in points:
            payload = point.get("payload")
            if not isinstance(point.get("id"), int) or not isinstance(point.get("vector"), list) or not isinstance(payload, dict):
                raise ProviderUnavailable("invalid_vector_point")
            if set(payload) - {"class_id", "material_id", "knowledge_entry_id", "chunk_id", "chunk_index"}:
                raise ProviderUnavailable("invalid_vector_payload")
        self._request(f"/collections/{self.collection_name}/points?wait=true", {"points": points})

    def delete(self, point_ids: list[int]) -> None:
        if point_ids:
            self._request(f"/collections/{self.collection_name}/points/delete?wait=true", {"points": point_ids})

    def search(self, vector: list[float], class_id: int, limit: int) -> list[dict[str, Any]]:
        response = self._request(f"/collections/{self.collection_name}/points/search", {
            "vector": vector, "limit": limit, "with_payload": True,
            "filter": {"must": [{"key": "class_id", "match": {"value": class_id}}]},
        })
        result = response.get("result")
        if not isinstance(result, list):
            raise ProviderUnavailable("invalid_vector_response")
        return result
