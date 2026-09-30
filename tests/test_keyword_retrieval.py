from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data


def setup(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'keyword.sqlite3'}",
                      "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"), "TOKEN_SIGNING_SECRET": "secret"})
    seed_data(app)
    return app


def auth(client, account):
    login = client.post("/login", json={"account": account, "password": f"{account}-password"})
    return {"Authorization": f"Bearer {login.json['access_token']}"}


def test_keyword_finds_chinese_same_class_chunk_without_vector_calls(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher = auth(client, "teacher-a")
    uploaded = client.post("/api/materials", json={"display_name": "化学讲义", "content": "化学反应速率由温度影响。"}, headers=teacher)
    assert uploaded.status_code == 201

    class NoCalls:
        def embed(self, texts): raise AssertionError("keyword must not embed")
        def search(self, vector, class_id, limit): raise AssertionError("keyword must not search vectors")

    app.extensions["embedding_provider"] = NoCalls()
    app.extensions["vector_store"] = NoCalls()
    student = auth(client, "student-a")
    response = client.get("/api/retrieval?q=化学反应&mode=keyword", headers=student)
    assert response.status_code == 200
    assert response.json["hits"][0]["material_title"] == "化学讲义"
    assert response.json["hits"][0]["excerpt"].startswith("化学反应")
    assert "vector" not in response.json["hits"][0]


def test_keyword_does_not_return_foreign_class_text(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher_b = auth(client, "teacher-b")
    assert client.post("/api/materials", json={"display_name": "密文", "content": "跨班级保密词"}, headers=teacher_b).status_code == 201
    student_a = auth(client, "student-a")
    response = client.get("/api/retrieval?q=跨班级保密词&mode=keyword&class_id=2", headers=student_a)
    assert response.status_code == 200
    assert response.json["hits"] == []

