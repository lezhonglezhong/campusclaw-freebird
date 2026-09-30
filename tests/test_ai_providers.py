import pytest

from campusclaw.ai_providers import OpenAIChatProvider, OpenAIEmbeddingProvider, ProviderUnavailable, serialize_content_parts
from campusclaw.runtime_config import GatewaySettings


def settings() -> GatewaySettings:
    return GatewaySettings("sqlite://", "http://qdrant", "https://gateway/v1", "key", "course-embedding", "https://gateway/v1", "key", "course-chat", 3, 2048)


def test_embedding_appends_path_and_sends_only_model_and_input() -> None:
    calls = []
    def transport(url, payload, key, timeout):
        calls.append((url, payload, key, timeout))
        return {"data": [{"index": 0, "embedding": [0.0] * 2048}]}
    assert OpenAIEmbeddingProvider(settings(), transport).embed(["hello"]) == [[0.0] * 2048]
    assert calls == [("https://gateway/v1/embeddings", {"model": "course-embedding", "input": ["hello"]}, "key", 3)]


def test_embedding_rejects_invalid_dimension() -> None:
    provider = OpenAIEmbeddingProvider(settings(), lambda *_: {"data": [{"index": 0, "embedding": [1]}]})
    with pytest.raises(ProviderUnavailable, match="dimension"):
        provider.embed(["hello"])


def test_chat_appends_path_and_uses_course_model() -> None:
    calls = []
    def transport(url, payload, key, timeout):
        calls.append((url, payload, key, timeout))
        return {"choices": [{"message": {"content": "answer [1]"}}]}
    result = OpenAIChatProvider(settings(), transport).answer("rules", "question", [], [{"citation": 1, "title": "T", "chunk_index": 0, "text": "source"}])
    assert result == "answer [1]"
    assert calls[0][0] == "https://gateway/v1/chat/completions"
    assert calls[0][1]["model"] == "course-chat"


def test_image_url_serializer_is_provider_boundary_only() -> None:
    parts = serialize_content_parts([
        {"type": "text", "text": "look"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}},
    ])
    assert parts[1] == {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}


def test_chat_payload_over_20mb_never_reaches_transport() -> None:
    provider = OpenAIChatProvider(settings(), lambda *_: (_ for _ in ()).throw(AssertionError("network called")))
    with pytest.raises(ProviderUnavailable, match="too_large"):
        provider.answer("rules", "x" * (21 * 1024 * 1024), [], [])
