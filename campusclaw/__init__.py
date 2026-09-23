"""CampusClaw application package."""

from pathlib import Path
from typing import Mapping
import os

from flask import Flask, jsonify

from campusclaw.auth import auth_bp
from campusclaw.db import init_db
from campusclaw.materials import materials_bp
from campusclaw.seed import register_seed_command


def create_app(test_config: Mapping[str, object] | None = None) -> Flask:
    """Create the Flask application and initialize local persistence."""
    app = Flask(__name__, instance_relative_config=True)
    database_path = Path(app.instance_path) / "campusclaw.sqlite3"
    app.config.from_mapping(
        DATABASE_URL=f"sqlite:///{database_path}",
        MATERIAL_STORAGE_DIR=str(Path(app.instance_path) / "materials"),
        SESSION_SECRET=os.environ.get("SESSION_SECRET"),
        TESTING=False,
    )

    if test_config is not None:
        app.config.update(test_config)

    if not app.config["SESSION_SECRET"]:
        raise RuntimeError("SESSION_SECRET must be configured")
    app.secret_key = app.config["SESSION_SECRET"]
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db(app)
    register_seed_command(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(materials_bp)

    @app.get("/health")
    def health_check():
        """Provide an unauthenticated, minimal liveness response."""
        return jsonify(status="ok")

    return app
