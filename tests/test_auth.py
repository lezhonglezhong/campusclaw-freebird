"""Authentication endpoint tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import User
from campusclaw.seed import SEED_ACCOUNTS, seed_data


def make_client(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'auth.sqlite3'}",
        "SESSION_SECRET": "test-session-secret",
    })
    seed_data(app)
    return app, app.test_client()


def test_login_contract_and_password_hashing(tmp_path: Path) -> None:
    app, client = make_client(tmp_path)
    response = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})

    assert response.status_code == 200
    assert response.json["user"] == {"id": 1, "account": "teacher-a", "role": "teacher", "class_id": 1}
    with client.session_transaction() as session:
        assert session["user_id"] == 1
    user = app.extensions["sqlalchemy"]["session"].query(User).filter_by(account="teacher-a").one()
    assert user.password_hash != SEED_ACCOUNTS["teacher-a"]["password"]


def test_unauthenticated_materials_redirects_and_invalid_login_has_no_session(tmp_path: Path) -> None:
    _app, client = make_client(tmp_path)

    response = client.get("/materials", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    response = client.post("/login", json={"account": "teacher-a", "password": "wrong"})
    assert response.status_code == 401
    with client.session_transaction() as session:
        assert "user_id" not in session


def test_responses_do_not_expose_session_secret(tmp_path: Path) -> None:
    _app, client = make_client(tmp_path)
    secret = "test-session-secret"
    for response in (client.get("/materials"), client.post("/login", json={"account": "unknown", "password": "bad"})):
        assert secret not in response.get_data(as_text=True)
