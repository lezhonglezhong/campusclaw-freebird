"""Runtime authentication configuration tests."""

from pathlib import Path

import pytest

from campusclaw import create_app


def test_missing_token_configuration_fails_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TOKEN_SIGNING_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="TOKEN_SIGNING_SECRET"):
        create_app({"TESTING": True})


def test_token_ttl_defaults_to_one_hour(tmp_path: Path) -> None:
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'default-ttl.sqlite3'}",
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    assert app.config["TOKEN_TTL_SECONDS"] == 3600


@pytest.mark.parametrize("ttl", [0, -1, 86401, "not-an-integer", True])
def test_invalid_token_ttl_fails_startup(tmp_path: Path, ttl: object) -> None:
    with pytest.raises(RuntimeError, match="TOKEN_TTL_SECONDS"):
        create_app({
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{tmp_path / 'invalid-ttl.sqlite3'}",
            "TOKEN_SIGNING_SECRET": "test-token-secret",
            "TOKEN_TTL_SECONDS": ttl,
        })


def test_token_compose_and_example_contain_no_real_secret() -> None:
    root = Path(__file__).parents[1]
    compose = (root / "compose.yaml").read_text()
    example = (root / ".env.example").read_text()
    combined = compose + example
    assert "TOKEN_SIGNING_SECRET" in compose and "TOKEN_SIGNING_SECRET" in example
    assert "TOKEN_TTL_SECONDS" in compose and "TOKEN_TTL_SECONDS" in example
    assert "SESSION_SECRET" not in combined
    assert "test-token-secret" not in combined


def test_gateway_configuration_uses_course_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    from campusclaw.runtime_config import load_gateway_settings
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://gateway.example/v1/")
    monkeypatch.setenv("EMBEDDING_API_KEY", "private")
    settings = load_gateway_settings()
    assert settings.embedding_base_url == "https://gateway.example/v1"
    assert settings.embedding_model == "course-embedding"
    assert settings.chat_model == "course-chat"
    assert settings.embedding_dim == 2048
