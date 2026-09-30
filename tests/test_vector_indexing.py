"""Vector orchestration keeps failed chunks keyword-ready and unpointed."""

from pathlib import Path

from campusclaw import create_app
from campusclaw.ai_providers import ProviderUnavailable
from campusclaw.knowledge_indexing import ensure_material_knowledge, vectorize_entry
from campusclaw.models import Class, Material, User


class FakeStore:
    def __init__(self):
        self.points = []
        self.deleted = []

    def ensure_collection(self):
        pass

    def upsert(self, points):
        self.points.extend(points)

    def delete(self, point_ids):
        self.deleted.extend(point_ids)


def make_entry(tmp_path: Path):
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'vectors.sqlite3'}", "TOKEN_SIGNING_SECRET": "secret"})
    session = app.extensions["sqlalchemy"]["session"]
    classroom = Class(name="A")
    teacher = User(account="t", password_hash="hash", role="teacher", class_=classroom)
    material = Material(display_name="lesson", class_=classroom, uploader=teacher, content_path="unused", status="ready")
    session.add(material)
    session.flush()
    entry = ensure_material_knowledge(session, material, "x" * 900)
    session.flush()
    return session, entry


def test_vector_ids_and_payload_are_relational_only(tmp_path):
    session, entry = make_entry(tmp_path)
    store = FakeStore()

    class Embedder:
        def embed(self, texts):
            return [[0.0] * 2048]

    vectorize_entry(session, entry, Embedder(), store)
    assert entry.vector_status == "ready"
    assert len(store.points) == len(entry.chunks)
    for point in store.points:
        assert point["id"] == point["payload"]["chunk_id"]
        assert set(point["payload"]) == {"class_id", "material_id", "knowledge_entry_id", "chunk_id", "chunk_index"}
        assert "text" not in point["payload"]


def test_failed_embedding_creates_no_point(tmp_path):
    session, entry = make_entry(tmp_path)
    store = FakeStore()

    class FailingEmbedder:
        def embed(self, texts):
            raise ProviderUnavailable("unavailable")

    vectorize_entry(session, entry, FailingEmbedder(), store)
    assert entry.vector_status == "failed"
    assert all(chunk.text_status == "ready" and chunk.vector_status == "failed" for chunk in entry.chunks)
    assert store.points == []
