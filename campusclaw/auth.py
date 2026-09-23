"""Authentication endpoints and helpers."""

from functools import wraps

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash

from campusclaw.models import User


auth_bp = Blueprint("auth", __name__)


def user_payload(user: User) -> dict[str, int | str]:
    """Return the public identity fields specified by the login contract."""
    return {
        "id": user.id,
        "account": user.account,
        "role": user.role,
        "class_id": user.class_id,
        "class_name": user.class_.name,
    }


def session_user() -> User | None:
    """Resolve the current user from the signed session and persistence layer."""
    user_id = session.get("user_id")
    if not isinstance(user_id, int):
        return None
    return current_app.extensions["sqlalchemy"]["session"].get(User, user_id)


def require_authenticated_api(view):
    """Require a server-validated user for an API endpoint."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = session_user()
        if user is None:
            return jsonify(error="unauthorized"), 401
        return view(user, *args, **kwargs)
    return wrapped


def require_teacher(view):
    """Require the authenticated API user to have the teacher role."""
    @require_authenticated_api
    @wraps(view)
    def wrapped(user: User, *args, **kwargs):
        if user.role != "teacher":
            return jsonify(error="forbidden"), 403
        return view(user, *args, **kwargs)
    return wrapped


@auth_bp.post("/login")
def login():
    """Authenticate an account and establish its server-signed session."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="invalid_request"), 400
    account = payload.get("account")
    password = payload.get("password")
    if not isinstance(account, str) or not account or not isinstance(password, str) or not password:
        return jsonify(error="invalid_request"), 400

    db_session = current_app.extensions["sqlalchemy"]["session"]
    user = db_session.query(User).filter_by(account=account).one_or_none()
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify(error="invalid_credentials"), 401

    session.clear()
    session["user_id"] = user.id
    return jsonify(user=user_payload(user))


@auth_bp.get("/api/me")
def current_user():
    """Return the server-validated identity used by browser page initialization."""
    user = session_user()
    if user is None:
        return jsonify(error="unauthorized"), 401
    return jsonify(user=user_payload(user))


@auth_bp.post("/logout")
def logout():
    """Clear the signed browser session without exposing session contents."""
    session.clear()
    return "", 204


@auth_bp.get("/materials")
def materials_page():
    """Render the protected browser material workspace shell."""
    if session_user() is None:
        return redirect("/login")
    return render_template("materials.html")


@auth_bp.get("/login")
def login_page():
    """Render the public browser login page."""
    return render_template("login.html")
