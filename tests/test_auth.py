"""Authentication endpoint tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import User
from campusclaw.seed import SEED_ACCOUNTS, seed_data


def make_client(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'auth.sqlite3'}",
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    seed_data(app)
    return app, app.test_client()


def test_login_contract_and_password_hashing(tmp_path: Path) -> None:
    app, client = make_client(tmp_path)
    response = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})

    assert response.status_code == 200
    assert response.json["user"] == {
        "id": 1, "account": "teacher-a", "role": "teacher", "class_id": 1, "class_name": "A",
    }
    assert response.json["token_type"] == "Bearer"
    assert response.json["expires_in"] == 3600
    assert isinstance(response.json["access_token"], str)
    assert response.json["access_token"]
    assert "Set-Cookie" not in response.headers
    user = app.extensions["sqlalchemy"]["session"].query(User).filter_by(account="teacher-a").one()
    assert user.password_hash != SEED_ACCOUNTS["teacher-a"]["password"]


def test_b_class_seeded_accounts_can_log_in(tmp_path: Path) -> None:
    _app, client = make_client(tmp_path)
    response = client.post("/login", json={"account": "teacher-b", "password": "teacher-b-password"})
    assert response.status_code == 200
    assert response.json["user"]["role"] == "teacher"
    assert response.json["user"]["class_name"] == "B"
    me = client.get("/api/me", headers={"Authorization": f"Bearer {response.json['access_token']}"})
    assert me.status_code == 200
    assert me.json["user"]["account"] == "teacher-b"


def test_materials_is_public_shell_and_invalid_login_has_no_token(tmp_path: Path) -> None:
    _app, client = make_client(tmp_path)

    response = client.get("/materials", follow_redirects=False)
    assert response.status_code == 200
    assert b"teacher-a" not in response.data

    response = client.post("/login", json={"account": "teacher-a", "password": "wrong"})
    assert response.status_code == 401
    assert "access_token" not in response.get_json()
    assert "Set-Cookie" not in response.headers
    assert "access_token" not in response.json
    assert "Set-Cookie" not in response.headers


def test_responses_do_not_expose_session_secret(tmp_path: Path) -> None:
    _app, client = make_client(tmp_path)
    secret = "test-token-secret"
    for response in (client.get("/materials"), client.post("/login", json={"account": "unknown", "password": "bad"})):
        assert secret not in response.get_data(as_text=True)
