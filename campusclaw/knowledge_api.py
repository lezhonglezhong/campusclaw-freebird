"""Bearer-authenticated knowledge retrieval and answer API."""

from flask import Blueprint, current_app, jsonify, request

from campusclaw.auth import require_authenticated_api
from campusclaw.knowledge_retrieval import hybrid_retrieve, keyword_retrieve, public_hit, vector_retrieve
from campusclaw.ai_providers import ProviderUnavailable
from campusclaw.models import User


knowledge_bp = Blueprint("knowledge", __name__, url_prefix="/api")


def parse_ask_payload(payload: object) -> tuple[str, list[dict[str, str]]]:
    """Accept only the current question and bounded user/assistant history."""
    if not isinstance(payload, dict):
        raise ValueError("invalid_request")
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip() or len(question) > 500:
        raise ValueError("invalid_question")
    raw_history = payload.get("history", [])
    if not isinstance(raw_history, list):
        raise ValueError("invalid_history")
    history: list[dict[str, str]] = []
    for message in raw_history[-20:]:
        if not isinstance(message, dict):
            raise ValueError("invalid_history")
        role, content = message.get("role"), message.get("content")
        if role not in {"user", "assistant"}:
            continue
        if not isinstance(content, str) or not content.strip():
            raise ValueError("invalid_history")
        history.append({"role": role, "content": content.strip()[:1000]})
    return question.strip(), history[-6:]


@knowledge_bp.post("/ask")
@require_authenticated_api
def ask_knowledge(user: User):
    try:
        question, history = parse_ask_payload(request.get_json(silent=True))
    except ValueError:
        return jsonify(error="invalid_request"), 400
    session = current_app.extensions["sqlalchemy"]["session"]
    try:
        hits = hybrid_retrieve(
            session, question, user.class_id,
            current_app.extensions["embedding_provider"],
            current_app.extensions["vector_store"],
            limit=4,
        )
    except ProviderUnavailable:
        return jsonify(error="vector_unavailable"), 503
    return jsonify(error="answer_unavailable"), 503


@knowledge_bp.get("/retrieval")
@require_authenticated_api
def retrieve_chunks(user: User):
    query = request.args.get("q", "").strip()
    mode = request.args.get("mode", "hybrid")
    if not query or len(query) > 500 or mode not in {"keyword", "vector", "hybrid"}:
        return jsonify(error="invalid_query"), 400
    session = current_app.extensions["sqlalchemy"]["session"]
    if mode == "keyword":
        hits = keyword_retrieve(session, query, user.class_id)
    elif mode == "vector":
        try:
            hits = vector_retrieve(
                session, query, user.class_id,
                current_app.extensions["embedding_provider"],
                current_app.extensions["vector_store"],
            )
        except ProviderUnavailable:
            return jsonify(error="vector_unavailable"), 503
    else:
        try:
            hits = hybrid_retrieve(
                session, query, user.class_id,
                current_app.extensions["embedding_provider"],
                current_app.extensions["vector_store"],
            )
        except ProviderUnavailable:
            return jsonify(error="vector_unavailable"), 503
    return jsonify(mode=mode, hits=[public_hit(session, hit) for hit in hits])

