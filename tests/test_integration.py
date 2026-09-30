"""End-to-end coverage for the seeded authorization workflow."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def test_seeded_auth_upload_and_class_isolation_flow(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'integration.sqlite3'}", "MATERIAL_STORAGE_DIR": str(tmp_path / "content"), "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)

    anonymous = app.test_client()
    assert anonymous.get("/materials").status_code == 200
    assert anonymous.get("/api/materials").status_code == 401

    teacher = app.test_client()
    teacher_login = teacher.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    assert teacher_login.status_code == 200
    teacher.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {teacher_login.json['access_token']}"
    created = teacher.post("/api/materials", json={"display_name": "Integration notes", "content": "notes"})
    assert created.status_code == 201
    material_id = created.json["material"]["id"]
    listed = teacher.get("/api/materials?class_id=2")
    assert listed.status_code == 200
    assert {item["class_id"] for item in listed.json["materials"]} == {1}
    assert material_id in {item["id"] for item in listed.json["materials"]}

    student = app.test_client()
    student_login = student.post("/login", json={"account": "student-a", "password": "student-a-password"})
    assert student_login.status_code == 200
    student.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {student_login.json['access_token']}"
    assert student.post("/api/materials", json={"display_name": "Denied", "content": "content"}).status_code == 403

    class_b_material = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=2).one()
    hidden = teacher.get(f"/api/materials/{class_b_material.id}")
    assert hidden.status_code == 404
    assert hidden.json == {"error": "not_found"}
