"""Browser token lifecycle endpoint tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def test_materials_shell_contains_no_protected_data(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'browser-shell.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    client = app.test_client()

    response = client.get("/materials")
    assert response.status_code == 200
    assert b"teacher-a" not in response.data
    assert b"student-a" not in response.data
    assert b"access_token" not in response.data


def test_current_user_and_logout_use_bearer_token(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'browser-token.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    client = app.test_client()

    assert client.get("/api/me").status_code == 401
    login = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json['access_token']}"}
    assert client.get("/api/me", headers=headers).json == {"user": login.json["user"]}

    logout = client.post("/logout")
    assert logout.status_code == 204
    assert "Set-Cookie" not in logout.headers
    assert client.get("/api/me", headers=headers).status_code == 200
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/materials").status_code == 401


def test_cookie_only_fallback_is_rejected(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'cookie.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    client = app.test_client()
    client.set_cookie("session", "legacy-session-value")

    response = client.get("/api/materials")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
