"""Class-scoped material read endpoints."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_file
from sqlalchemy import text
from werkzeug.utils import secure_filename

from campusclaw.auth import require_authenticated_api, require_teacher
from campusclaw.models import Material, User
from campusclaw.knowledge_indexing import ensure_material_knowledge, vectorize_entry
from campusclaw.knowledge_indexing import replace_material_chunks
from campusclaw.chunking import ChunkingError, chunk_text
from campusclaw.models import KnowledgeEntry
from campusclaw.ai_providers import ProviderUnavailable
from campusclaw.retrieval import index_material, remove_material_from_index


materials_bp = Blueprint("materials", __name__, url_prefix="/api/materials")


@materials_bp.post("/<int:material_id>/reindex")
@require_teacher
def reindex_material(user: User, material_id: int):
    """Rebuild an own-class source index from its retained original body."""
    db_session = current_app.extensions["sqlalchemy"]["session"]
    material = db_session.query(Material).filter_by(id=material_id, class_id=user.class_id).one_or_none()
    if material is None:
        return jsonify(error="not_found"), 404
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="invalid_request"), 400
    strategy = payload.get("strategy", "auto")
    options = payload.get("options", {})
    if not isinstance(options, dict) or not isinstance(strategy, str):
        return jsonify(error="invalid_strategy"), 400
    entry = db_session.query(KnowledgeEntry).filter_by(material_id=material.id).one_or_none()
    try:
        body = entry.body_text if entry is not None else Path(material.content_path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return jsonify(error="source_unavailable"), 503
    try:
        planned_chunks = chunk_text(body, strategy, options)
    except ChunkingError:
        return jsonify(error="invalid_strategy"), 400
    if entry is None:
        entry = ensure_material_knowledge(db_session, material, body)
    old_ids = [chunk.id for chunk in entry.chunks if chunk.vector_status == "ready"]
    store = current_app.extensions["vector_store"]
    try:
        if old_ids:
            store.delete(old_ids)
        replace_material_chunks(db_session, entry, planned_chunks, strategy, options)
        vectorize_entry(db_session, entry, current_app.extensions["embedding_provider"], store)
        db_session.commit()
    except Exception:
        db_session.rollback()
        return jsonify(error="indexing_failed"), 503
    return jsonify(
        material_id=material.id, strategy=strategy, chunk_count=len(entry.chunks),
        text_status=entry.text_status, vector_status=entry.vector_status,
    )


@materials_bp.get("/retrieve")
@require_authenticated_api
def retrieve_materials(user: User):
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify(error="invalid_query"), 400
    session = current_app.extensions["sqlalchemy"]["session"]
    try:
        rows = session.execute(text("""
            SELECT m.id, m.display_name, m.class_id, c.name, m.uploader_id,
                   snippet(material_retrieval, 2, '', '', '…', 24)
            FROM material_retrieval JOIN materials m ON m.id = material_retrieval.material_id
            JOIN classes c ON c.id = m.class_id
            WHERE material_retrieval MATCH :query AND material_retrieval.class_id = :class_id
            ORDER BY bm25(material_retrieval)
        """), {"query": query, "class_id": user.class_id}).all()
    except Exception:
        return jsonify(error="invalid_query"), 400
    if not rows:
        rows = session.execute(text("""
            SELECT m.id, m.display_name, m.class_id, c.name, m.uploader_id,
                   material_retrieval.content
            FROM material_retrieval JOIN materials m ON m.id = material_retrieval.material_id
            JOIN classes c ON c.id = m.class_id
            WHERE material_retrieval.class_id = :class_id
              AND material_retrieval.content LIKE :pattern
            ORDER BY m.id
        """), {"class_id": user.class_id, "pattern": f"%{query}%"}).all()
    return jsonify(results=[{
        "material_id": row[0], "display_name": row[1], "class_id": row[2],
        "class_name": row[3], "uploader_id": row[4], "excerpt": row[5][:240],
        "download_url": f"/api/materials/{row[0]}/download",
    } for row in rows])


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
    suffix = content_path.suffix.lower() if content_path.suffix.lower() in {".txt", ".md"} else ".txt"
    download_name = material.display_name if material.display_name.lower().endswith(suffix) else f"{material.display_name}{suffix}"
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
        ready_ids = [
            chunk.id for chunk in material.knowledge_entry.chunks
            if chunk.vector_status == "ready"
        ] if material.knowledge_entry is not None else []
        if ready_ids:
            current_app.extensions["vector_store"].delete(ready_ids)
        if content_path.is_file():
            staged_path = content_path.with_name(f".{content_path.name}.{uuid4().hex}.deleting")
            os.replace(content_path, staged_path)
        db_session.delete(material)
        remove_material_from_index(db_session, material.id)
        db_session.commit()
        if staged_path is not None:
            staged_path.unlink()
    except ProviderUnavailable:
        db_session.rollback()
        return jsonify(error="vector_store_unavailable"), 503
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
        db_session.flush()
        index_material(db_session, material, content)
        entry = ensure_material_knowledge(db_session, material, content)
        vectorize_entry(
            db_session, entry, current_app.extensions["embedding_provider"],
            current_app.extensions["vector_store"],
        )
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
