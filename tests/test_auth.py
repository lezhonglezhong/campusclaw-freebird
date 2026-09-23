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
