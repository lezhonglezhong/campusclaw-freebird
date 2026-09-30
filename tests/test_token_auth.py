"""Focused tests for JWT access-token configuration and behavior."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest

from campusclaw import create_app
from campusclaw.auth import (
    TokenAuthenticationError,
    decode_access_token,
    issue_access_token,
    require_authenticated_api,
)
from campusclaw.models import User
from campusclaw.seed import seed_data


def token_app(tmp_path: Path):
    return create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'tokens.sqlite3'}",
        "TOKEN_SIGNING_SECRET": "test-token-secret",
        "TOKEN_TTL_SECONDS": 3600,
    })


def seeded_token_app(tmp_path: Path):
    app = token_app(tmp_path)
    seed_data(app)
    return app


def login_headers(client, account: str = "teacher-a", password: str = "teacher-a-password") -> dict[str, str]:
    response = client.post("/login", json={"account": account, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['access_token']}"}


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


def test_token_claims_are_limited_to_identity_and_lifetime(tmp_path: Path) -> None:
    app = token_app(tmp_path)
    with app.app_context():
        encoded = issue_access_token(42)
        payload = jwt.decode(
            encoded,
            "test-token-secret",
            algorithms=["HS256"],
        )

    assert set(payload) == {"jti", "sub", "iat", "exp"}
    assert payload["sub"] == "42"
    assert payload["exp"] - payload["iat"] == 3600


def test_expired_token_maps_to_stable_authentication_failure(tmp_path: Path) -> None:
    app = token_app(tmp_path)
    now = datetime.now(timezone.utc)
    encoded = jwt.encode(
        {"jti": "expired", "sub": "1", "iat": now - timedelta(minutes=2), "exp": now - timedelta(minutes=1)},
        "test-token-secret",
        algorithm="HS256",
    )

    with app.app_context(), pytest.raises(TokenAuthenticationError):
        decode_access_token(encoded)


def test_malformed_token_maps_to_stable_authentication_failure(tmp_path: Path) -> None:
    app = token_app(tmp_path)
    with app.app_context(), pytest.raises(TokenAuthenticationError):
        decode_access_token("not-a-jwt")


def test_incorrect_signature_maps_to_stable_authentication_failure(tmp_path: Path) -> None:
    app = token_app(tmp_path)
    now = datetime.now(timezone.utc)
    encoded = jwt.encode(
        {"jti": "forged", "sub": "1", "iat": now, "exp": now + timedelta(minutes=5)},
        "wrong-secret",
        algorithm="HS256",
    )

    with app.app_context(), pytest.raises(TokenAuthenticationError):
        decode_access_token(encoded)


def assert_unauthorized(response) -> None:
    assert response.status_code == 401
    assert response.json == {"error": "unauthorized"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_missing_bearer_header_is_rejected_uniformly(tmp_path: Path) -> None:
    app = seeded_token_app(tmp_path)
    assert_unauthorized(app.test_client().get("/api/materials"))


@pytest.mark.parametrize("header", ["", "Basic abc", "Bearer", "Bearer one two", "Bearer one,two"])
def test_malformed_bearer_header_is_rejected_uniformly(tmp_path: Path, header: str) -> None:
    app = seeded_token_app(tmp_path)
    assert_unauthorized(app.test_client().get("/api/materials", headers={"Authorization": header}))


def test_expired_bearer_token_is_rejected_uniformly(tmp_path: Path) -> None:
    app = seeded_token_app(tmp_path)
    now = datetime.now(timezone.utc)
    encoded = jwt.encode(
        {"jti": "expired", "sub": "1", "iat": now - timedelta(minutes=2), "exp": now - timedelta(minutes=1)},
        "test-token-secret",
        algorithm="HS256",
    )
    assert_unauthorized(app.test_client().get("/api/materials", headers={"Authorization": f"Bearer {encoded}"}))


def test_bad_signature_bearer_token_is_rejected_uniformly(tmp_path: Path) -> None:
    app = seeded_token_app(tmp_path)
    now = datetime.now(timezone.utc)
    encoded = jwt.encode(
        {"jti": "forged", "sub": "1", "iat": now, "exp": now + timedelta(minutes=5)},
        "wrong-secret",
        algorithm="HS256",
    )
    assert_unauthorized(app.test_client().get("/api/materials", headers={"Authorization": f"Bearer {encoded}"}))


def test_unknown_user_bearer_token_is_rejected_uniformly(tmp_path: Path) -> None:
    app = seeded_token_app(tmp_path)
    with app.app_context():
        encoded = issue_access_token(99999)
    assert_unauthorized(app.test_client().get("/api/materials", headers={"Authorization": f"Bearer {encoded}"}))


def test_bearer_resolver_reloads_user_from_database(tmp_path: Path) -> None:
    app = seeded_token_app(tmp_path)

    @app.get("/_resolved-user")
    @require_authenticated_api
    def resolved_user(user: User):
        return {"role": user.role, "class_id": user.class_id}

    client = app.test_client()
    headers = login_headers(client)
    db_session = app.extensions["sqlalchemy"]["session"]
    user = db_session.query(User).filter_by(account="teacher-a").one()
    user.role = "student"
    user.class_id = 2
    db_session.commit()

    response = client.get("/_resolved-user", headers=headers)
    assert response.status_code == 200
    assert response.json == {"role": "student", "class_id": 2}
