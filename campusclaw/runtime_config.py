"""Validated, server-only runtime settings for external course services."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


MAX_GATEWAY_REQUEST_BYTES = 20 * 1024 * 1024
DEFAULT_EMBEDDING_DIM = 2048


class ConfigurationError(RuntimeError):
    """Raised when a deployment setting is malformed."""


def _positive_int(value: object, name: str, default: int) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        raise ConfigurationError(f"{name} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{name} must be a positive integer") from exc
    if parsed < 1:
        raise ConfigurationError(f"{name} must be a positive integer")
    return parsed


@dataclass(frozen=True)
class GatewaySettings:
    """External service settings; credentials deliberately stay server-side."""

    database_url: str
    qdrant_url: str | None
    embedding_base_url: str | None
    embedding_api_key: str | None
    embedding_model: str
    chat_base_url: str | None
    chat_api_key: str | None
    chat_model: str
    timeout_seconds: int
    embedding_dim: int


def load_gateway_settings(environ: Mapping[str, str] | None = None) -> GatewaySettings:
    """Read configuration without requiring a gateway to be enabled in tests."""
    env = os.environ if environ is None else environ
    database_url = env.get("DATABASE_URL", "").strip()
    if not database_url:
        database_url = "sqlite:///campusclaw.sqlite3"
    dimension = _positive_int(env.get("EMBEDDING_DIM"), "EMBEDDING_DIM", DEFAULT_EMBEDDING_DIM)
    if dimension != DEFAULT_EMBEDDING_DIM:
        raise ConfigurationError("EMBEDDING_DIM must be 2048")
    timeout = _positive_int(env.get("GATEWAY_TIMEOUT_SECONDS"), "GATEWAY_TIMEOUT_SECONDS", 10)
    embedding_base = env.get("EMBEDDING_BASE_URL", "").strip().rstrip("/") or None
    chat_base = env.get("CHAT_BASE_URL", "").strip().rstrip("/") or embedding_base
    embedding_key = env.get("EMBEDDING_API_KEY", "").strip() or None
    chat_key = env.get("CHAT_API_KEY", "").strip() or embedding_key
    return GatewaySettings(
        database_url=database_url,
        qdrant_url=env.get("QDRANT_URL", "").strip().rstrip("/") or None,
        embedding_base_url=embedding_base,
        embedding_api_key=embedding_key,
        embedding_model=env.get("EMBEDDING_MODEL", "course-embedding").strip() or "course-embedding",
        chat_base_url=chat_base,
        chat_api_key=chat_key,
        chat_model=env.get("CHAT_MODEL", "course-chat").strip() or "course-chat",
        timeout_seconds=timeout,
        embedding_dim=dimension,
    )
