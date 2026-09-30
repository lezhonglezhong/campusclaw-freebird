from pathlib import Path

import pytest

from campusclaw import create_app
from campusclaw.models import KnowledgeChunk
from campusclaw.seed import seed_data


def test_hybrid_default_fuses_ranks_and_omits_weak_points(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'hybrid.sqlite3'}",
                      "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"), "TOKEN_SIGNING_SECRET": "secret"})
    seed_data(app)
    client = app.test_client()
    login = client.post("/login", json={"account": "teacher-a", "password": "teacher-a-password"})
    headers = {"Authorization": f"Bearer {login.json['access_token']}"}
    created = client.post("/api/materials", json={"display_name": "Other", "content": "different text"}, headers=headers)
    assert created.status_code == 201
    session = app.extensions["sqlalchemy"]["session"]
    own = session.query(KnowledgeChunk).filter_by(class_id=1).order_by(KnowledgeChunk.id).all()
    for chunk in own:
        chunk.vector_status = "ready"
    session.commit()

    class Embedder:
        def embed(self, texts): return [[0.0] * 2048]

    class Store:
        def search(self, vector, class_id, limit):
            return [{"id": own[1].id, "score": 0.9}, {"id": own[0].id, "score": 0.8},
                    {"id": 999, "score": 0.1}]

    app.extensions["embedding_provider"] = Embedder()
    app.extensions["vector_store"] = Store()
    response = client.get("/api/retrieval?q=Class", headers=headers)
    assert response.status_code == 200
    assert response.json["mode"] == "hybrid"
    hits = response.json["hits"]
    assert hits[0]["chunk_id"] == own[0].id
    assert hits[0]["keyword_rank"] == 1
    assert hits[0]["vector_rank"] == 2
    assert hits[0]["rrf_score"] == pytest.approx(1 / 61 + 1 / 62)
    assert hits[0]["rrf_score"] > hits[1]["rrf_score"]
    assert len(hits[0]["excerpt"]) <= 240

