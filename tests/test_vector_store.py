import pytest

from campusclaw.ai_providers import ProviderUnavailable
from campusclaw.runtime_config import GatewaySettings
from campusclaw.vector_store import QdrantVectorStore


def settings() -> GatewaySettings:
    return GatewaySettings("sqlite://", "http://qdrant", None, None, "course-embedding", None, None, "course-chat", 3, 2048)


def test_vector_store_uses_identifier_only_payload() -> None:
    calls = []
    def transport(url, payload, key, timeout):
        calls.append((url, payload))
        return {"result": []}
    store = QdrantVectorStore(settings(), transport)
    store.ensure_collection()
    store.upsert([{ "id": 5, "vector": [0.0] * 2048, "payload": {"class_id": 1, "material_id": 2, "knowledge_entry_id": 3, "chunk_id": 5, "chunk_index": 0}}])
    assert calls[0][1]["vectors"] == {"size": 2048, "distance": "Cosine"}
    assert calls[1][1]["points"][0]["payload"]["chunk_id"] == 5


def test_vector_store_rejects_text_payload() -> None:
    store = QdrantVectorStore(settings(), lambda *_: {"result": []})
    with pytest.raises(ProviderUnavailable):
        store.upsert([{ "id": 5, "vector": [], "payload": {"text": "secret"}}])
