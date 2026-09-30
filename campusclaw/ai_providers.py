"""Small injectable OpenAI-compatible embedding and chat adapters."""

from __future__ import annotations

import json
import math
from numbers import Real
from typing import Any, Callable, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from campusclaw.runtime_config import GatewaySettings, MAX_GATEWAY_REQUEST_BYTES


class ProviderUnavailable(RuntimeError):
    """An external provider cannot safely supply a valid result."""


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class ChatProvider(Protocol):
    def answer(
        self, system_instruction: str, question: str, history: list[dict[str, str]], sources: list[dict[str, Any]]
    ) -> str: ...


Transport = Callable[[str, dict[str, Any], str, int], dict[str, Any]]


def _check_payload_size(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_GATEWAY_REQUEST_BYTES:
        raise ProviderUnavailable("gateway_request_too_large")


def serialize_content_parts(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate OpenAI-compatible text and future image_url message parts."""
    serialized = []
    for part in parts:
        if not isinstance(part, dict):
            raise ProviderUnavailable("invalid_chat_message")
        if part.get("type") == "text" and isinstance(part.get("text"), str):
            serialized.append({"type": "text", "text": part["text"]})
        elif part.get("type") == "image_url" and isinstance(part.get("image_url"), dict):
            url = part["image_url"].get("url")
            if not isinstance(url, str) or not url:
                raise ProviderUnavailable("invalid_chat_message")
            serialized.append({"type": "image_url", "image_url": {"url": url}})
        else:
            raise ProviderUnavailable("invalid_chat_message")
    return serialized


def _post_json(url: str, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
    _check_payload_size(payload)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = Request(url, data=encoded, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - configured course endpoint
            if not 200 <= response.status < 300:
                raise ProviderUnavailable("gateway_unavailable")
            decoded = json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, ValueError, UnicodeDecodeError) as exc:
        raise ProviderUnavailable("gateway_unavailable") from exc
    if not isinstance(decoded, dict):
        raise ProviderUnavailable("invalid_gateway_response")
    return decoded


class OpenAIEmbeddingProvider:
    def __init__(self, settings: GatewaySettings, transport: Transport = _post_json) -> None:
        self.settings, self.transport = settings, transport

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.settings.embedding_base_url or not self.settings.embedding_api_key:
            raise ProviderUnavailable("embedding_unavailable")
        if not texts or any(not isinstance(text, str) for text in texts):
            raise ProviderUnavailable("invalid_embedding_input")
        payload = {"model": self.settings.embedding_model, "input": texts}
        _check_payload_size(payload)
        response = self.transport(
            f"{self.settings.embedding_base_url}/embeddings", payload,
            self.settings.embedding_api_key, self.settings.timeout_seconds,
        )
        data = response.get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise ProviderUnavailable("invalid_embedding_response")
        ordered = sorted(data, key=lambda item: item.get("index", -1) if isinstance(item, dict) else -1)
        vectors: list[list[float]] = []
        for expected_index, item in enumerate(ordered):
            vector = item.get("embedding") if isinstance(item, dict) else None
            if item.get("index", expected_index) != expected_index or not isinstance(vector, list):
                raise ProviderUnavailable("invalid_embedding_response")
            if len(vector) != self.settings.embedding_dim or any(isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) for value in vector):
                raise ProviderUnavailable("invalid_embedding_dimension")
            vectors.append([float(value) for value in vector])
        return vectors


class OpenAIChatProvider:
    def __init__(self, settings: GatewaySettings, transport: Transport = _post_json) -> None:
        self.settings, self.transport = settings, transport

    def answer(
        self, system_instruction: str, question: str, history: list[dict[str, str]], sources: list[dict[str, Any]]
    ) -> str:
        if not self.settings.chat_base_url or not self.settings.chat_api_key:
            raise ProviderUnavailable("chat_unavailable")
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_instruction}]
        messages.extend(history)
        source_text = "\n\n".join(
            f"[{source['citation']}] {source['title']} / chunk {source['chunk_index']}\n{source['text']}"
            for source in sources
        )
        messages.append({"role": "user", "content": f"Question: {question}\n\nSources:\n{source_text}"})
        payload = {"model": self.settings.chat_model, "messages": messages}
        _check_payload_size(payload)
        response = self.transport(
            f"{self.settings.chat_base_url}/chat/completions",
            payload,
            self.settings.chat_api_key, self.settings.timeout_seconds,
        )
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ProviderUnavailable("invalid_chat_response")
        message = choices[0].get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ProviderUnavailable("invalid_chat_response")
        return content.strip()
