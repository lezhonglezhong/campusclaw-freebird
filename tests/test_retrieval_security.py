from pathlib import Path

from campusclaw import create_app
from campusclaw.seed import seed_data
from campusclaw.models import KnowledgeChunk


def test_missing_bearer_never_returns_chunks(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'security.sqlite3'}",
                      "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"), "TOKEN_SIGNING_SECRET": "secret"})
    seed_data(app)
    client = app.test_client()
    for mode in ("keyword", "vector", "hybrid"):
        response = client.get(f"/api/retrieval?q=sample&mode={mode}")
        assert response.status_code == 401
        assert "hits" not in response.json


def test_class_override_and_foreign_point_never_leak_source_data(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'isolation.sqlite3'}",
                      "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"), "TOKEN_SIGNING_SECRET": "secret"})
    seed_data(app)
    session = app.extensions["sqlalchemy"]["session"]
    foreign = session.query(KnowledgeChunk).filter_by(class_id=2).one()
    foreign_id = foreign.id
    foreign.vector_status = "ready"
    session.commit()

    class Embedder:
        def embed(self, texts): return [[0.0] * 2048]

    class Store:
        def search(self, vector, class_id, limit):
            return [{"id": foreign_id, "score": 0.99, "payload": {"body": "foreign secret"}}]

    app.extensions["embedding_provider"] = Embedder()
    app.extensions["vector_store"] = Store()
    client = app.test_client()
    login = client.post("/login", json={"account": "student-a", "password": "student-a-password"})
    headers = {"Authorization": f"Bearer {login.json['access_token']}", "X-Class-ID": "2"}
    for mode in ("keyword", "vector", "hybrid"):
        response = client.get(f"/api/retrieval?q=Class B&mode={mode}&class_id=2", headers=headers)
        assert response.status_code == 200
        assert response.json["hits"] == []
        body = response.get_data(as_text=True)
        for forbidden in ("foreign secret", "seed-class-b", "embedding", "sk-", "content_path"):
            assert forbidden not in body

