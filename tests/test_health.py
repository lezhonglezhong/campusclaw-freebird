"""Unauthenticated application and Compose health-check tests."""

from pathlib import Path

from campusclaw import create_app


def test_health_endpoint_is_public_and_minimal(tmp_path: Path) -> None:
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'health.sqlite3'}",
        "SESSION_SECRET": "test-secret",
    })

    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_compose_healthcheck_calls_health_endpoint() -> None:
    compose = (Path(__file__).parents[1] / "compose.yaml").read_text()

    assert "healthcheck:" in compose
    assert "http://127.0.0.1:8000/health" in compose


def test_dockerfile_uses_verified_python_registry_proxy() -> None:
    dockerfile = (Path(__file__).parents[1] / "Dockerfile").read_text()

    assert dockerfile.startswith("FROM docker.m.daocloud.io/library/python:3.13-slim")
