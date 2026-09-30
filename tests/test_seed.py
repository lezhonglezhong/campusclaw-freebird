"""Development seed-data tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Class, Material, User
from campusclaw.seed import SEED_ACCOUNTS, seed_data
from werkzeug.security import check_password_hash


def test_seed_is_idempotent(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'seed.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    seed_data(app)
    session = app.extensions["sqlalchemy"]["session"]

    assert [item.name for item in session.query(Class).order_by(Class.name)] == ["A", "B"]
    assert session.query(User).count() == 4
    assert session.query(Material).count() == 2
    assert {item.class_.name for item in session.query(Material)} == {"A", "B"}
    assert {item.account: item.class_.name for item in session.query(User)} == {
        "teacher-a": "A", "student-a": "A", "teacher-b": "B", "student-b": "B",
    }
    assert {item.class_.name: item.uploader.account for item in session.query(Material)} == {
        "A": "teacher-a", "B": "teacher-b",
    }


def test_seeded_passwords_are_hashed(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'seed.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    session = app.extensions["sqlalchemy"]["session"]

    for account, details in SEED_ACCOUNTS.items():
        user = session.query(User).filter_by(account=account).one()
        assert user.password_hash != details["password"]
        assert check_password_hash(user.password_hash, details["password"])
