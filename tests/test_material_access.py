"""Class-scoped material read tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def logged_in_client(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'materials.sqlite3'}", "SESSION_SECRET": "test-secret"})
    seed_data(app)
    client = app.test_client()
    client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    return app, client


def test_class_a_user_lists_and_reads_class_a_material(tmp_path: Path) -> None:
    app, client = logged_in_client(tmp_path)
    response = client.get("/api/materials")
    assert response.status_code == 200
    assert response.json["materials"]
    assert {item["class_id"] for item in response.json["materials"]} == {1}

    material = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=1).one()
    response = client.get(f"/api/materials/{material.id}")
    assert response.status_code == 200
    assert response.json["material"]["id"] == material.id
