"""Runtime secret configuration tests."""

from pathlib import Path

import pytest

from campusclaw import create_app


def test_missing_session_secret_fails_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        create_app({"TESTING": True})


def test_compose_and_example_contain_no_real_secret() -> None:
    root = Path(__file__).parents[1]
    compose = (root / "compose.yaml").read_text()
    example = (root / ".env.example").read_text()
    assert "SESSION_SECRET" in compose and "SESSION_SECRET" in example
    assert "test-session-secret" not in compose + example
