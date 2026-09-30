"""Bearer-authenticated knowledge retrieval and answer API."""

from flask import Blueprint, current_app, jsonify, request

from campusclaw.auth import require_authenticated_api
from campusclaw.knowledge_retrieval import keyword_retrieve, public_hit
from campusclaw.models import User


knowledge_bp = Blueprint("knowledge", __name__, url_prefix="/api")


@knowledge_bp.get("/retrieval")
@require_authenticated_api
def retrieve_chunks(user: User):
    query = request.args.get("q", "").strip()
    mode = request.args.get("mode", "hybrid")
    if not query or len(query) > 500 or mode not in {"keyword", "vector", "hybrid"}:
        return jsonify(error="invalid_query"), 400
    if mode != "keyword":
        return jsonify(error="vector_unavailable"), 503
    session = current_app.extensions["sqlalchemy"]["session"]
    hits = keyword_retrieve(session, query, user.class_id)
    return jsonify(mode=mode, hits=[public_hit(session, hit) for hit in hits])

