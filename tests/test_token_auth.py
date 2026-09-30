"""Focused tests for JWT access-token configuration and behavior."""

from pathlib import Path

import pytest

from campusclaw import create_app


def test_explicit_token_configuration_is_normalized(tmp_path: Path) -> None:
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'token-config.sqlite3'}",
        "TOKEN_SIGNING_SECRET": "test-token-secret",
        "TOKEN_TTL_SECONDS": "7200",
    })

    assert app.config["TOKEN_SIGNING_SECRET"] == "test-token-secret"
    assert app.config["TOKEN_TTL_SECONDS"] == 7200


@pytest.mark.parametrize("ttl", [0, -30, 86401, "bad"])
def test_token_ttl_configuration_rejects_invalid_values(tmp_path: Path, ttl: object) -> None:
    with pytest.raises(RuntimeError, match="TOKEN_TTL_SECONDS"):
        create_app({
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bad-token-config.sqlite3'}",
            "TOKEN_SIGNING_SECRET": "test-token-secret",
            "TOKEN_TTL_SECONDS": ttl,
        })
