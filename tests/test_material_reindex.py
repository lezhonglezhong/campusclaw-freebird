"""Teacher reindexing validates before replacing a class-owned index."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.models import KnowledgeEntry, Material
from campusclaw.seed import seed_data


class FakeStore:
    def __init__(self):
        self.deleted = []
        self.points = []
    def ensure_collection(self): pass
    def upsert(self, points): self.points.extend(points)
    def delete(self, point_ids): self.deleted.extend(point_ids)


class FakeEmbedder:
    def embed(self, texts): return [[0.0] * 2048 for _ in texts]


def setup(tmp_path: Path):
    app = create_app({
        "TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'reindex.sqlite3'}",
        "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"),
        "TOKEN_SIGNING_SECRET": "secret",
    })
    seed_data(app)
    app.extensions["embedding_provider"] = FakeEmbedder()
    app.extensions["vector_store"] = FakeStore()
    return app


def headers(client, account):
    login = client.post("/login", json={"account": account, "password": f"{account}-password"})
    return {"Authorization": f"Bearer {login.json['access_token']}"}


def test_teacher_reindexes_without_changing_original_body(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    auth = headers(client, "teacher-a")
    session = app.extensions["sqlalchemy"]["session"]
    material = session.query(Material).filter_by(class_id=1).one()
    entry = session.query(KnowledgeEntry).filter_by(material_id=material.id).one()
    original = entry.body_text
    old_ids = [chunk.id for chunk in entry.chunks]
    response = client.post(f"/api/materials/{material.id}/reindex", json={
        "strategy": "custom", "options": {"max_length": 100, "overlap_percent": 0}
    }, headers=auth)
    assert response.status_code == 200
    session.expire_all()
    assert entry.body_text == original
    assert entry.strategy == "custom"
    assert [chunk.id for chunk in entry.chunks] != old_ids
    assert response.json["vector_status"] == "ready"


def test_invalid_strategy_preserves_existing_chunks(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    auth = headers(client, "teacher-a")
    session = app.extensions["sqlalchemy"]["session"]
    material = session.query(Material).filter_by(class_id=1).one()
    before = [chunk.id for chunk in material.knowledge_entry.chunks]
    response = client.post(f"/api/materials/{material.id}/reindex", json={
        "strategy": "custom", "options": {"max_length": 20}
    }, headers=auth)
    assert response.status_code == 400
    session.expire_all()
    assert [chunk.id for chunk in material.knowledge_entry.chunks] == before


def test_student_forbidden_and_foreign_material_hidden(tmp_path):
    app = setup(tmp_path)
    client = app.test_client()
    session = app.extensions["sqlalchemy"]["session"]
    class_b = session.query(Material).filter_by(class_id=2).one()
    teacher_auth = headers(client, "teacher-a")
    assert client.post(f"/api/materials/{class_b.id}/reindex", json={}, headers=teacher_auth).status_code == 404
    student_auth = headers(client, "student-a")
    assert client.post(f"/api/materials/{class_b.id}/reindex", json={}, headers=student_auth).status_code == 403

