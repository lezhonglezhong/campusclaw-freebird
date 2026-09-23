"""Persistence-model tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Class, Material, User


def test_models_create_and_relate_class_user_and_material(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'models.sqlite3'}", "SESSION_SECRET": "test-secret"})
    session = app.extensions["sqlalchemy"]["session"]
    class_a = Class(name="A")
    teacher = User(account="teacher-a", password_hash="hash", role="teacher", class_=class_a)
    material = Material(
        display_name="Lesson", class_=class_a, uploader=teacher,
        content_path="/materials/lesson.txt", status="ready",
    )
    session.add(material)
    session.commit()

    stored = session.get(Material, material.id)
    assert stored is not None
    assert stored.class_.name == "A"
    assert stored.uploader.account == "teacher-a"
