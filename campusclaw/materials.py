"""Class-scoped material read endpoints."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_file
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


@materials_bp.get("/<int:material_id>/download")
@require_authenticated_api
def download_material(user: User, material_id: int):
    """Send an own-class material as an attachment without exposing its path."""
    db_session = current_app.extensions["sqlalchemy"]["session"]
    material = db_session.query(Material).filter_by(id=material_id, class_id=user.class_id).one_or_none()
    if material is None:
        return jsonify(error="not_found"), 404
    content_path = Path(material.content_path)
    if not content_path.is_file():
        return jsonify(error="not_found"), 404
    download_name = secure_filename(material.display_name) or "material.txt"
    return send_file(content_path, as_attachment=True, download_name=download_name)


@materials_bp.delete("/<int:material_id>")
@require_teacher
def delete_material(user: User, material_id: int):
    """Delete an own-class material and its content without crossing class boundaries."""
    db_session = current_app.extensions["sqlalchemy"]["session"]
    material = db_session.query(Material).filter_by(id=material_id, class_id=user.class_id).one_or_none()
    if material is None:
        return jsonify(error="not_found"), 404

    content_path = Path(material.content_path)
    staged_path: Path | None = None
    try:
        if content_path.is_file():
            staged_path = content_path.with_name(f".{content_path.name}.{uuid4().hex}.deleting")
            os.replace(content_path, staged_path)
        db_session.delete(material)
        db_session.commit()
        if staged_path is not None:
            staged_path.unlink()
    except OSError:
        db_session.rollback()
        if staged_path is not None and staged_path.exists():
            os.replace(staged_path, content_path)
        return jsonify(error="storage_failed"), 500
    except Exception:
        db_session.rollback()
        if staged_path is not None and staged_path.exists():
            os.replace(staged_path, content_path)
        return jsonify(error="deletion_failed"), 500
    return "", 204


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
        filename = secure_filename(uploaded_file.filename or "")
        suffix = Path(filename).suffix.lower()
        if not filename or suffix not in {".txt", ".md"}:
            return jsonify(error="invalid_request"), 400
        supplied_name = request.form.get("display_name")
        if supplied_name is None:
            display_name = filename
        else:
            display_name = supplied_name.strip()
            if not display_name:
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
