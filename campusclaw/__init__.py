"""CampusClaw application package."""

from pathlib import Path
from typing import Mapping

from flask import Flask

from campusclaw.db import init_db
from campusclaw.seed import register_seed_command


def create_app(test_config: Mapping[str, object] | None = None) -> Flask:
    """Create the Flask application and initialize local persistence."""
    app = Flask(__name__, instance_relative_config=True)
    database_path = Path(app.instance_path) / "campusclaw.sqlite3"
    app.config.from_mapping(
        DATABASE_URL=f"sqlite:///{database_path}",
        TESTING=False,
    )

    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db(app)
    register_seed_command(app)
    return app
