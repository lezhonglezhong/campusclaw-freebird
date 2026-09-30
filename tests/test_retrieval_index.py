from pathlib import Path

from sqlalchemy import text

from campusclaw import create_app


def test_sqlite_knowledge_fts_index_is_bootstrapped(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'fts.sqlite3'}", "TOKEN_SIGNING_SECRET": "secret"})
    session = app.extensions["sqlalchemy"]["session"]
    assert session.execute(text("SELECT count(*) FROM knowledge_chunk_retrieval")).scalar_one() == 0
