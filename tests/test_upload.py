"""Teacher material-upload tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def app_and_client(tmp_path: Path, account: str = "teacher-a"):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'upload.sqlite3'}", "MATERIAL_STORAGE_DIR": str(tmp_path / "content"), "SESSION_SECRET": "test-secret"})
    seed_data(app)
    client = app.test_client()
    password = "teacher-a-password" if account == "teacher-a" else "student-a-password"
    client.post("/login", json={"account": account, "password": password})
    return app, client


def test_teacher_upload_creates_class_owned_local_material(tmp_path: Path) -> None:
    app, client = app_and_client(tmp_path)
    response = client.post("/api/materials", json={"display_name": "Notes", "content": "lesson content"})
    assert response.status_code == 201
    material = app.extensions["sqlalchemy"]["session"].get(Material, response.json["material"]["id"])
    assert material.class_id == 1 and material.uploader_id == 1
    assert Path(material.content_path).read_text() == "lesson content"


def test_student_upload_is_403_and_creates_no_record(tmp_path: Path) -> None:
    app, client = app_and_client(tmp_path, "student-a")
    before = app.extensions["sqlalchemy"]["session"].query(Material).count()
    response = client.post("/api/materials", json={"display_name": "Notes", "content": "lesson content"})
    assert response.status_code == 403
    assert app.extensions["sqlalchemy"]["session"].query(Material).count() == before


def test_failed_upload_leaves_no_record_or_file(tmp_path: Path) -> None:
    app, client = app_and_client(tmp_path)
    app.config["MATERIAL_STORAGE_DIR"] = str(tmp_path / "not-a-directory")
    Path(app.config["MATERIAL_STORAGE_DIR"]).write_text("block storage")
    before = app.extensions["sqlalchemy"]["session"].query(Material).count()
    response = client.post("/api/materials", json={"display_name": "Notes", "content": "lesson content"})
    assert response.status_code == 500
    assert app.extensions["sqlalchemy"]["session"].query(Material).count() == before
