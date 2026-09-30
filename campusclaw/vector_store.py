"""Identifier-only vector-store contract and Qdrant HTTP adapter."""

from __future__ import annotations

import json
import math
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from campusclaw.ai_providers import ProviderUnavailable
from campusclaw.runtime_config import GatewaySettings


class VectorStore(Protocol):
    def ensure_collection(self) -> None: ...
    def upsert(self, points: list[dict[str, Any]]) -> None: ...
    def delete(self, point_ids: list[int]) -> None: ...
    def search(self, vector: list[float], class_id: int, limit: int) -> list[dict[str, Any]]: ...


VectorTransport = Callable[[str, str, dict[str, Any] | None, int], dict[str, Any]]


def _qdrant_request(method: str, url: str, payload: dict[str, Any] | None, timeout: int) -> dict[str, Any]:
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8") if payload is not None else None
    request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, ValueError, UnicodeDecodeError) as exc:
        raise ProviderUnavailable("vector_store_unavailable") from exc
    if not isinstance(result, dict) or result.get("status") not in (None, "ok"):
        raise ProviderUnavailable("invalid_vector_response")
    return result


class QdrantVectorStore:
    collection_name = "campusclaw_chunks"
    payload_fields = {"class_id", "material_id", "knowledge_entry_id", "chunk_id", "chunk_index"}

    def __init__(self, settings: GatewaySettings, transport: VectorTransport = _qdrant_request) -> None:
        self.settings, self.transport = settings, transport

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.settings.qdrant_url:
            raise ProviderUnavailable("vector_store_unavailable")
        return self.transport(method, f"{self.settings.qdrant_url}{path}", payload, self.settings.timeout_seconds)

    def ensure_collection(self) -> None:
        path = f"/collections/{self.collection_name}"
        exists = self._request("GET", f"{path}/exists").get("result")
        if not isinstance(exists, dict) or not isinstance(exists.get("exists"), bool):
            raise ProviderUnavailable("invalid_vector_response")
        if not exists["exists"]:
            self._request("PUT", path, {"vectors": {"size": self.settings.embedding_dim, "distance": "Cosine"}})
        else:
            info = self._request("GET", path).get("result")
            config = info.get("config", {}) if isinstance(info, dict) else {}
            vectors = config.get("params", {}).get("vectors", {}) if isinstance(config, dict) else {}
            if vectors.get("size") != self.settings.embedding_dim or vectors.get("distance") != "Cosine":
                raise ProviderUnavailable("invalid_vector_collection")

    def upsert(self, points: list[dict[str, Any]]) -> None:
        for point in points:
            payload = point.get("payload")
            vector = point.get("vector")
            if (
                isinstance(point.get("id"), bool) or not isinstance(point.get("id"), int)
                or not isinstance(vector, list) or len(vector) != self.settings.embedding_dim
                or any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in vector)
                or not isinstance(payload, dict) or set(payload) != self.payload_fields
                or any(isinstance(value, bool) or not isinstance(value, int) for value in payload.values())
                or payload["chunk_id"] != point["id"]
            ):
                raise ProviderUnavailable("invalid_vector_point")
        if points:
            self._request("PUT", f"/collections/{self.collection_name}/points?wait=true", {"points": points})

    def delete(self, point_ids: list[int]) -> None:
        if point_ids:
            self._request("POST", f"/collections/{self.collection_name}/points/delete?wait=true", {"points": point_ids})

    def search(self, vector: list[float], class_id: int, limit: int) -> list[dict[str, Any]]:
        response = self._request("POST", f"/collections/{self.collection_name}/points/search", {
            "vector": vector, "limit": limit, "with_payload": True,
            "filter": {"must": [{"key": "class_id", "match": {"value": class_id}}]},
        })
        result = response.get("result")
        if not isinstance(result, list):
            raise ProviderUnavailable("invalid_vector_response")
        return result

