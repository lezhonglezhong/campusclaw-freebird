"""FTS index lifecycle coverage."""
from sqlalchemy import text
from campusclaw import create_app
from campusclaw.seed import seed_data


def test_seed_upload_and_delete_update_retrieval_index(tmp_path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'index.sqlite3'}", "TOKEN_SIGNING_SECRET": "test-token-secret"})
    seed_data(app)
    session = app.extensions["sqlalchemy"]["session"]
    assert session.execute(text("SELECT count(*) FROM material_retrieval")).scalar() == 2
    client = app.test_client()
    login = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {login.json['access_token']}"
    created = client.post("/api/materials", json={"display_name": "Indexed", "content": "searchable phrase"})
    material_id = created.json["material"]["id"]
    assert session.execute(text("SELECT content FROM material_retrieval WHERE material_id = :id"), {"id": material_id}).scalar() == "searchable phrase"
    assert client.delete(f"/api/materials/{material_id}").status_code == 204
    assert session.execute(text("SELECT count(*) FROM material_retrieval WHERE material_id = :id"), {"id": material_id}).scalar() == 0
