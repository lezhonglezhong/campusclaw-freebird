"""Development seed-data tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Class, Material, User
from campusclaw.seed import seed_data


def test_seed_is_idempotent(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'seed.sqlite3'}"})
    seed_data(app)
    seed_data(app)
    session = app.extensions["sqlalchemy"]["session"]

    assert [item.name for item in session.query(Class).order_by(Class.name)] == ["A", "B"]
    assert session.query(User).count() == 2
    assert session.query(Material).count() == 2
    assert {item.class_.name for item in session.query(Material)} == {"A", "B"}
