"""Teacher-only material deletion and content-cleanup tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def make_app(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'delete.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "content"),
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    seed_data(app)
    return app


def login(client, account: str, password: str) -> None:
    response = client.post("/login", json={"account": account, "password": password})
    assert response.status_code == 200
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {response.json['access_token']}"


def test_teacher_deletes_own_class_material_and_content(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    teacher = app.test_client()
    login(teacher, "teacher-a", "teacher-a-password")
    created = teacher.post("/api/materials", json={"display_name": "Remove me", "content": "content"})
    material_id = created.json["material"]["id"]
    material = app.extensions["sqlalchemy"]["session"].get(Material, material_id)
    content_path = Path(material.content_path)

    response = teacher.delete(f"/api/materials/{material_id}")

    assert response.status_code == 204
    assert app.extensions["sqlalchemy"]["session"].get(Material, material_id) is None
    assert not content_path.exists()


def test_student_cannot_delete_and_cross_class_is_hidden(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    session = app.extensions["sqlalchemy"]["session"]
    class_a = session.query(Material).filter_by(class_id=1).one()
    class_b = session.query(Material).filter_by(class_id=2).one()
    student = app.test_client()
    teacher_b = app.test_client()
    login(student, "student-a", "student-a-password")
    login(teacher_b, "teacher-b", "teacher-b-password")

    denied = student.delete(f"/api/materials/{class_a.id}")
    hidden = teacher_b.delete(f"/api/materials/{class_a.id}")

    assert denied.status_code == 403
    assert hidden.status_code == 404
    assert session.get(Material, class_a.id) is not None
    assert Path(class_a.content_path).exists()
    assert session.get(Material, class_b.id) is not None


def test_failed_database_deletion_restores_staged_content(tmp_path: Path, monkeypatch) -> None:
    app = make_app(tmp_path)
    teacher = app.test_client()
    login(teacher, "teacher-a", "teacher-a-password")
    session = app.extensions["sqlalchemy"]["session"]
    material = session.query(Material).filter_by(class_id=1).one()
    material_id = material.id
    content_path = Path(material.content_path)

    def fail_commit():
        raise RuntimeError("database failure")

    monkeypatch.setattr(session, "commit", fail_commit)
    response = teacher.delete(f"/api/materials/{material_id}")

    assert response.status_code == 500
    assert session.get(Material, material_id) is not None
    assert content_path.read_text(encoding="utf-8") == "Class A sample material content.\n"
