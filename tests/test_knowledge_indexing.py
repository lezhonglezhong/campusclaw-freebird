from pathlib import Path

from campusclaw import create_app
from campusclaw.models import KnowledgeEntry
from campusclaw.seed import seed_data


def test_seed_creates_one_source_first_index_per_material(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'index.sqlite3'}", "MATERIAL_STORAGE_DIR": str(tmp_path / "materials"), "TOKEN_SIGNING_SECRET": "secret"})
    seed_data(app); seed_data(app)
    session = app.extensions["sqlalchemy"]["session"]
    entries = session.query(KnowledgeEntry).all()
    assert len(entries) == 2
    assert all(entry.chunks and entry.vector_status == "pending" for entry in entries)
