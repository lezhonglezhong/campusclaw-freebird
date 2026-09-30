"""CampusClaw application package."""

from pathlib import Path
from typing import Mapping
import os

from flask import Flask, jsonify

from campusclaw.auth import auth_bp
from campusclaw.db import init_db
from campusclaw.materials import materials_bp
from campusclaw.seed import register_seed_command


DEFAULT_TOKEN_TTL_SECONDS = 3600
MAX_TOKEN_TTL_SECONDS = 86400


def _validate_token_config(app: Flask) -> None:
    """Normalize and validate server-only access-token configuration."""
    signing_secret = app.config.get("TOKEN_SIGNING_SECRET")
    if not isinstance(signing_secret, str) or not signing_secret.strip():
        raise RuntimeError("TOKEN_SIGNING_SECRET must be configured")

    raw_ttl = app.config.get("TOKEN_TTL_SECONDS", DEFAULT_TOKEN_TTL_SECONDS)
    if isinstance(raw_ttl, bool):
        raise RuntimeError("TOKEN_TTL_SECONDS must be a positive integer no greater than 86400")
    try:
        token_ttl = int(raw_ttl)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "TOKEN_TTL_SECONDS must be a positive integer no greater than 86400"
        ) from exc
    if not 1 <= token_ttl <= MAX_TOKEN_TTL_SECONDS:
        raise RuntimeError("TOKEN_TTL_SECONDS must be a positive integer no greater than 86400")

    app.config["TOKEN_SIGNING_SECRET"] = signing_secret
    app.config["TOKEN_TTL_SECONDS"] = token_ttl


def create_app(test_config: Mapping[str, object] | None = None) -> Flask:
    """Create the Flask application and initialize local persistence."""
    app = Flask(__name__, instance_relative_config=True)
    database_path = Path(app.instance_path) / "campusclaw.sqlite3"
    app.config.from_mapping(
        DATABASE_URL=f"sqlite:///{database_path}",
        MATERIAL_STORAGE_DIR=str(Path(app.instance_path) / "materials"),
        SESSION_SECRET=os.environ.get("SESSION_SECRET"),
        TOKEN_SIGNING_SECRET=os.environ.get("TOKEN_SIGNING_SECRET"),
        TOKEN_TTL_SECONDS=os.environ.get("TOKEN_TTL_SECONDS", DEFAULT_TOKEN_TTL_SECONDS),
        TESTING=False,
    )

    if test_config is not None:
        app.config.update(test_config)

    _validate_token_config(app)
    app.secret_key = app.config.get("SESSION_SECRET") or app.config["TOKEN_SIGNING_SECRET"]
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
