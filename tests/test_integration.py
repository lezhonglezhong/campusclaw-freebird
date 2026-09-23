"""End-to-end coverage for the seeded authorization workflow."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def test_seeded_auth_upload_and_class_isolation_flow(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'integration.sqlite3'}", "MATERIAL_STORAGE_DIR": str(tmp_path / "content"), "SESSION_SECRET": "test-secret"})
    seed_data(app)

    anonymous = app.test_client()
    assert anonymous.get("/materials").status_code == 302

    teacher = app.test_client()
    assert teacher.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"}).status_code == 200
    created = teacher.post("/api/materials", json={"display_name": "Integration notes", "content": "notes"})
    assert created.status_code == 201
    material_id = created.json["material"]["id"]
    listed = teacher.get("/api/materials?class_id=2")
    assert listed.status_code == 200
    assert {item["class_id"] for item in listed.json["materials"]} == {1}
    assert material_id in {item["id"] for item in listed.json["materials"]}

    student = app.test_client()
    assert student.post("/login", json={"account": "student-a", "password": "student-a-password"}).status_code == 200
    assert student.post("/api/materials", json={"display_name": "Denied", "content": "content"}).status_code == 403

    class_b_material = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=2).one()
    hidden = teacher.get(f"/api/materials/{class_b_material.id}")
    assert hidden.status_code == 404
    assert hidden.json == {"error": "not_found"}
