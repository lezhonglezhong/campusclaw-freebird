"""SQLAlchemy setup shared by CampusClaw persistence code."""

from flask import Flask
from sqlalchemy import Engine, create_engine
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

    @app.teardown_appcontext
    def remove_session(_exception: BaseException | None = None) -> None:
        session.remove()
