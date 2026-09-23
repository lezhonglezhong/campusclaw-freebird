"""Runtime secret configuration tests."""

from pathlib import Path

import pytest

from campusclaw import create_app


def test_missing_session_secret_fails_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        create_app({"TESTING": True})
