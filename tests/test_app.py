"""Baseline application tests for the initial scaffold."""

from pathlib import Path

from sqlalchemy import text

from campusclaw import create_app


def test_application_uses_configured_sqlite_persistence(tmp_path: Path) -> None:
    database_path = tmp_path / "test.sqlite3"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{database_path}",
            "TOKEN_SIGNING_SECRET": "test-token-secret",
        }
    )

    persistence = app.extensions["sqlalchemy"]
    assert persistence["engine"].dialect.name == "sqlite"

    with persistence["engine"].connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
