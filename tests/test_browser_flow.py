"""End-to-end browser-facing workflow coverage using Flask clients."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def make_app(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'browser-flow.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "content"),
        "SESSION_SECRET": "test-secret",
    })
    seed_data(app)
    return app


def login(client, account: str, password: str) -> None:
    response = client.post("/login", json={"account": account, "password": password})
    assert response.status_code == 200


def test_browser_login_session_recovery_protected_page_and_logout(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    client = app.test_client()

    assert client.get("/materials").status_code == 302
    login(client, "teacher-a", "teacher-a-password")
    assert client.get("/materials").status_code == 200
    assert client.get("/api/me").json["user"]["role"] == "teacher"
    assert client.post("/logout").status_code == 204
    assert client.get("/materials").status_code == 302
    assert client.get("/api/me").status_code == 401


def test_teacher_browser_flow_uploads_and_lists_own_class_material(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    teacher = app.test_client()
    login(teacher, "teacher-a", "teacher-a-password")

    uploaded = teacher.post("/api/materials", json={"display_name": "Browser notes", "content": "content"})
    assert uploaded.status_code == 201
    listed = teacher.get("/api/materials")
    assert uploaded.json["material"]["id"] in {item["id"] for item in listed.json["materials"]}
    assert {item["class_id"] for item in listed.json["materials"]} == {1}
    material_id = uploaded.json["material"]["id"]
    assert teacher.get(f"/api/materials/{material_id}/download").data == b"content"
    assert teacher.delete(f"/api/materials/{material_id}").status_code == 204
    assert app.extensions["sqlalchemy"]["session"].get(Material, material_id) is None


def test_student_browser_flow_is_read_only_and_cannot_upload(tmp_path: Path) -> None:
    app = make_app(tmp_path)
    student = app.test_client()
    login(student, "student-a", "student-a-password")

    assert student.get("/materials").status_code == 200
    assert student.get("/api/me").json["user"]["role"] == "student"
    denied = student.post("/api/materials", json={"display_name": "Denied", "content": "content"})
    assert denied.status_code == 403
    assert denied.json == {"error": "forbidden"}
