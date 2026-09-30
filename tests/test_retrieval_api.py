from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def test_retrieval_requires_bearer_and_valid_query(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'api.sqlite3'}",
                      "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"), "TOKEN_SIGNING_SECRET": "secret"})
    seed_data(app)
    client = app.test_client()
    assert client.get("/api/retrieval?q=class").status_code == 401
    login = client.post("/login", json={"account": "student-a", "password": "student-a-password"})
    headers = {"Authorization": f"Bearer {login.json['access_token']}"}
    assert client.get("/api/retrieval?q=   &mode=keyword", headers=headers).status_code == 400
    assert client.get("/api/retrieval?q=x&mode=unknown", headers=headers).status_code == 400
    assert client.get("/api/retrieval?q=class&mode=keyword", headers=headers).json["mode"] == "keyword"

