"""SQLAlchemy setup shared by CampusClaw persistence code."""

from flask import Flask
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    """Base class for persistence models added by later tasks."""


def init_db(app: Flask) -> None:
    """Attach a SQLite-capable SQLAlchemy engine and scoped session to *app*."""
    engine: Engine = create_engine(app.config["DATABASE_URL"])
    session = scoped_session(sessionmaker(bind=engine))
    app.extensions["sqlalchemy"] = {
        "engine": engine,
        "session": session,
    }

    # Importing here registers the persistence models before their tables are
    # created, while keeping the model module free of Flask application setup.
    from campusclaw import models  # noqa: F401

    Base.metadata.create_all(engine)
    initialize_knowledge_index(session, engine.dialect.name)
    from campusclaw.retrieval import initialize_retrieval_index
    initialize_retrieval_index(session)
    session.commit()

    @app.teardown_appcontext
    def remove_session(_exception: BaseException | None = None) -> None:
        session.remove()


def initialize_knowledge_index(session, dialect: str) -> None:
    """Create the local FTS companion only where the dialect supports it."""
    if dialect == "sqlite":
        session.execute(text(
            "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_chunk_retrieval "
            "USING fts5(chunk_id UNINDEXED, class_id UNINDEXED, chunk_text)"
        ))
    elif dialect == "mysql":
        exists = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() AND table_name = 'knowledge_chunks' "
            "AND index_name = 'idx_knowledge_chunks_text_ngram'"
        )).scalar_one()
        if not exists:
            session.execute(text(
                "CREATE FULLTEXT INDEX idx_knowledge_chunks_text_ngram "
                "ON knowledge_chunks (chunk_text) WITH PARSER ngram"
            ))
