"""Class-scoped material read endpoints."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from campusclaw.auth import require_authenticated_api, require_teacher
from campusclaw.models import Material, User


materials_bp = Blueprint("materials", __name__, url_prefix="/api/materials")


def material_payload(material: Material) -> dict[str, int | str]:
    return {
        "id": material.id,
        "display_name": material.display_name,
        "class_id": material.class_id,
        "class_name": material.class_.name,
        "uploader_id": material.uploader_id,
        "status": material.status,
    }


@materials_bp.get("")
@require_authenticated_api
def list_materials(user: User):
    db_session = current_app.extensions["sqlalchemy"]["session"]
    query = request.args.get("q", "")
    materials_query = db_session.query(Material).filter_by(class_id=user.class_id)
    if query:
        materials_query = materials_query.filter(Material.display_name.ilike(f"%{query}%"))
    materials = materials_query.order_by(Material.id).all()
    return jsonify(materials=[material_payload(material) for material in materials])


@materials_bp.get("/<int:material_id>")
@require_authenticated_api
def material_detail(user: User, material_id: int):
    db_session = current_app.extensions["sqlalchemy"]["session"]
    material = db_session.query(Material).filter_by(id=material_id, class_id=user.class_id).one_or_none()
    if material is None:
        return jsonify(error="not_found"), 404
    return jsonify(material=material_payload(material))


@materials_bp.post("")
@require_teacher
def upload_material(user: User):
    suffix = ".txt"
    if request.mimetype == "application/json":
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="invalid_request"), 400
        display_name, content = payload.get("display_name"), payload.get("content")
        if not isinstance(display_name, str) or not display_name or not isinstance(content, str) or not content:
            return jsonify(error="invalid_request"), 400
    else:
        uploaded_file = request.files.get("file")
        if uploaded_file is None:
            return jsonify(error="invalid_request"), 400
        display_name = secure_filename(uploaded_file.filename or "")
        suffix = Path(display_name).suffix.lower()
        if not display_name or suffix not in {".txt", ".md"}:
            return jsonify(error="invalid_request"), 400
        try:
            content = uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return jsonify(error="invalid_request"), 400
        if not content:
            return jsonify(error="invalid_request"), 400

    storage_dir = Path(current_app.config["MATERIAL_STORAGE_DIR"])
    temporary_path: Path | None = None
    final_path: Path | None = None
    db_session = current_app.extensions["sqlalchemy"]["session"]
    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=storage_dir, delete=False) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)
        final_path = storage_dir / f"{uuid4().hex}{suffix}"
        os.replace(temporary_path, final_path)
        material = Material(
            display_name=display_name,
            class_id=user.class_id,
            uploader_id=user.id,
            content_path=str(final_path),
            status="ready",
        )
        db_session.add(material)
        db_session.commit()
    except OSError:
        db_session.rollback()
        for path in (temporary_path, final_path):
            if path is not None:
                path.unlink(missing_ok=True)
        return jsonify(error="storage_failed"), 500
    except Exception:
        db_session.rollback()
        for path in (temporary_path, final_path):
            if path is not None:
                path.unlink(missing_ok=True)
        raise
    return jsonify(material=material_payload(material)), 201
