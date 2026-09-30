"""Full-title routing for bounded same-class chunk retrieval."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import KnowledgeChunk
from campusclaw.seed import seed_data


def setup(tmp_path: Path):
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": f"sqlite:///{tmp_path / 'title.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"),
        "TOKEN_SIGNING_SECRET": "test-token-secret",
    })
    seed_data(app)
    return app


def auth(client, account):
    response = client.post("/login", json={"account": account, "password": f"{account}-password"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['access_token']}"}


class WeakEmbedder:
    def embed(self, texts):
        return [[0.0] * 2048]


class WeakStore:
    def search(self, vector, class_id, limit):
        return []


def test_title_question_finds_short_numeric_text_in_keyword_and_hybrid(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher = auth(client, "teacher-a")
    created = client.post("/api/materials", json={"display_name": "A班资料", "content": "123456"}, headers=teacher)
    assert created.status_code == 201
    material_id = created.json["material"]["id"]

    class NoCalls:
        def embed(self, texts): raise AssertionError("keyword must not embed")
        def search(self, vector, class_id, limit): raise AssertionError("keyword must not search")

    app.extensions["embedding_provider"] = NoCalls()
    app.extensions["vector_store"] = NoCalls()
    query = "A班资料的内容是什么？"
    response = client.get("/api/retrieval", query_string={"q": query, "mode": "keyword"}, headers=teacher)
    assert response.status_code == 200
    assert response.json["hits"][0]["material_id"] == material_id
    assert response.json["hits"][0]["excerpt"] == "123456"
    assert response.json["hits"][0]["keyword_rank"] == 1
    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = WeakStore()
    response = client.get("/api/retrieval", query_string={"q": query, "mode": "hybrid"}, headers=teacher)
    assert response.status_code == 200
    assert response.json["hits"][0]["material_id"] == material_id


def test_foreign_title_short_title_and_unrelated_question_do_not_match(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher_b = auth(client, "teacher-b")
    assert client.post("/api/materials", json={"display_name": "B班机密材料", "content": "987654"}, headers=teacher_b).status_code == 201
    teacher_a = auth(client, "teacher-a")
    assert client.post("/api/materials", json={"display_name": "AB", "content": "123456"}, headers=teacher_a).status_code == 201
    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = WeakStore()
    for query in ("B班机密材料内容是什么？", "AB的内容是什么？", "今天有什么作业？"):
        for mode in ("keyword", "hybrid"):
            response = client.get("/api/retrieval", query_string={"q": query, "mode": mode}, headers=teacher_a)
            assert response.status_code == 200
            assert response.json["hits"] == []


def test_vector_only_keeps_similarity_cutoff_for_title_question(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    teacher = auth(client, "teacher-a")
    created = client.post("/api/materials", json={"display_name": "A班资料", "content": "123456"}, headers=teacher)
    assert created.status_code == 201
    material_id = created.json["material"]["id"]
    session = app.extensions["sqlalchemy"]["session"]
    chunk = session.query(KnowledgeChunk).filter_by(material_id=material_id).one()
    chunk.vector_status = "ready"
    session.commit()

    class Store:
        def search(self, vector, class_id, limit):
            return [{"id": chunk.id, "score": 0.34}]

    app.extensions["embedding_provider"] = WeakEmbedder()
    app.extensions["vector_store"] = Store()
    response = client.get("/api/retrieval", query_string={"q": "A班资料的内容是什么？", "mode": "vector"}, headers=teacher)
    assert response.status_code == 200
    assert response.json["hits"] == []
