from pathlib import Path

from campusclaw import create_app
from campusclaw.ai_providers import ProviderUnavailable
from campusclaw.models import KnowledgeChunk
from campusclaw.seed import seed_data


class Embedder:
    def embed(self, texts):
        return [[0.0] * 2048]


class Store:
    def __init__(self, points):
        self.points = points
        self.filters = []

    def search(self, vector, class_id, limit):
        self.filters.append(class_id)
        return self.points


def prepared_app(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'vector.sqlite3'}",
                      "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"), "TOKEN_SIGNING_SECRET": "secret"})
    seed_data(app)
    session = app.extensions["sqlalchemy"]["session"]
    for chunk in session.query(KnowledgeChunk):
        chunk.vector_status = "ready"
    session.commit()
    app.extensions["embedding_provider"] = Embedder()
    return app


def student_headers(client):
    login = client.post("/login", json={"account": "student-a", "password": "student-a-password"})
    return {"Authorization": f"Bearer {login.json['access_token']}"}


def test_vector_cutoff_and_db_class_recheck(tmp_path):
    app = prepared_app(tmp_path)
    session = app.extensions["sqlalchemy"]["session"]
    own = session.query(KnowledgeChunk).filter_by(class_id=1).one()
    foreign = session.query(KnowledgeChunk).filter_by(class_id=2).one()
    store = Store([
        {"id": foreign.id, "score": 0.99, "payload": {"text": "foreign secret"}},
        {"id": own.id, "score": 0.35},
        {"id": 99999, "score": 0.9},
        {"id": own.id, "score": 0.349},
    ])
    app.extensions["vector_store"] = store
    client = app.test_client()
    response = client.get("/api/retrieval?q=sample&mode=vector&class_id=2", headers=student_headers(client))
    assert response.status_code == 200
    assert store.filters == [1]
    assert [hit["chunk_id"] for hit in response.json["hits"]] == [own.id]
    assert response.json["hits"][0]["vector_score"] == 0.35
    assert "foreign secret" not in response.get_data(as_text=True)


def test_vector_dependency_failure_is_safe(tmp_path):
    app = prepared_app(tmp_path)
    class Broken:
        def search(self, vector, class_id, limit):
            raise ProviderUnavailable("secret-provider-body")
    app.extensions["vector_store"] = Broken()
    client = app.test_client()
    response = client.get("/api/retrieval?q=sample&mode=vector", headers=student_headers(client))
    assert response.status_code == 503
    assert response.json == {"error": "vector_unavailable"}

