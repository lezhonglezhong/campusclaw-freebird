"""Bearer-authenticated class-scoped material list tests."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import Material
from campusclaw.seed import seed_data


def logged_in_client(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'material-list.sqlite3'}",
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    seed_data(app)
    client = app.test_client()
    login = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {login.json['access_token']}"
    return app, client


def test_bearer_user_lists_and_reads_only_current_database_class(tmp_path: Path) -> None:
    app, client = logged_in_client(tmp_path)
    response = client.get("/api/materials?class_id=2")
    assert response.status_code == 200
    assert {item["class_id"] for item in response.json["materials"]} == {1}

    other_class = app.extensions["sqlalchemy"]["session"].query(Material).filter_by(class_id=2).one()
    hidden = client.get(f"/api/materials/{other_class.id}")
    assert hidden.status_code == 404
    assert hidden.json == {"error": "not_found"}


def test_material_list_requires_bearer_token(tmp_path: Path) -> None:
    app, _client = logged_in_client(tmp_path)
    response = app.test_client().get("/api/materials")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
