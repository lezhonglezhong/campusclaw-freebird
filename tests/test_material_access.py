"""Class-scoped material read tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def logged_in_client(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'materials.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    client = app.test_client()
    login = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {login.json['access_token']}"
    return app, client


def test_class_a_user_lists_and_reads_class_a_material(tmp_path: Path) -> None:
    app, client = logged_in_client(tmp_path)
    response = client.get("/api/materials")
    assert response.status_code == 200
    assert response.json["materials"]
    assert {item["class_id"] for item in response.json["materials"]} == {1}
    assert {item["class_name"] for item in response.json["materials"]} == {"A"}

    material = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=1).one()
    response = client.get(f"/api/materials/{material.id}")
    assert response.status_code == 200
    assert response.json["material"]["id"] == material.id
    assert response.json["material"]["class_name"] == "A"


def test_class_id_parameter_cannot_expand_list_scope(tmp_path: Path) -> None:
    _app, client = logged_in_client(tmp_path)
    response = client.get("/api/materials?class_id=2")
    assert response.status_code == 200
    assert {item["class_id"] for item in response.json["materials"]} == {1}


def test_cross_class_detail_returns_404_without_material_data(tmp_path: Path) -> None:
    app, client = logged_in_client(tmp_path)
    material = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=2).one()
    response = client.get(f"/api/materials/{material.id}")
    assert response.status_code == 404
    assert response.json == {"error": "not_found"}
