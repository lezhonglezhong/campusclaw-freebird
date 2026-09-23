"""Browser session support endpoint tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def test_current_user_and_logout_use_server_validated_session(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'browser-session.sqlite3'}", "SESSION_SECRET": "test-secret"})
    seed_data(app)
    client = app.test_client()

    assert client.get("/api/me").status_code == 401
    login = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    assert login.status_code == 200
    assert client.get("/api/me").json == {"user": login.json["user"]}

    assert client.post("/logout").status_code == 204
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/materials").status_code == 401
