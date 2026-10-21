"""Authentication endpoints and helpers."""

from datetime import datetime, timedelta, timezone
from functools import wraps
from uuid import uuid4

import jwt
from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.security import check_password_hash

from campusclaw.models import User


auth_bp = Blueprint("auth", __name__)


class TokenAuthenticationError(ValueError):
    """Represent any access-token failure without exposing its cause."""


def issue_access_token(user_id: int) -> str:
    """Issue a short-lived HS256 token containing identity-only claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "jti": str(uuid4()),
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=current_app.config["TOKEN_TTL_SECONDS"]),
    }
    return jwt.encode(
        payload,
        current_app.config["TOKEN_SIGNING_SECRET"],
        algorithm="HS256",
    )


def decode_access_token(token: str) -> int:
    """Verify an access token and return its integer user identifier."""
    try:
        payload = jwt.decode(
            token,
            current_app.config["TOKEN_SIGNING_SECRET"],
            algorithms=["HS256"],
            options={"require": ["jti", "sub", "iat", "exp"]},
        )
        subject = payload["sub"]
        if not isinstance(subject, str) or not subject.isdecimal():
            raise TokenAuthenticationError
        user_id = int(subject)
        if user_id <= 0:
            raise TokenAuthenticationError
        return user_id
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise TokenAuthenticationError from exc


def unauthorized_response():
    """Return the uniform Bearer challenge used by protected APIs."""
    response = jsonify(error="unauthorized")
    response.status_code = 401
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


def bearer_user() -> User | None:
    """Resolve a valid Authorization Bearer credential to the current DB user."""
    authorization_values = request.headers.getlist("Authorization")
    if len(authorization_values) != 1:
        return None
    parts = authorization_values[0].split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or "," in parts[1]:
        return None
    try:
        user_id = decode_access_token(parts[1])
    except TokenAuthenticationError:
        return None
    return current_app.extensions["sqlalchemy"]["session"].get(User, user_id)


def user_payload(user: User) -> dict[str, int | str]:
    """Return the public identity fields specified by the login contract."""
    return {
        "id": user.id,
        "account": user.account,
        "role": user.role,
        "class_id": user.class_id,
        "class_name": user.class_.name,
    }


def require_authenticated_api(view):
    """Require a Bearer token that resolves to a current database user."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = bearer_user()
        if user is None:
            return unauthorized_response()
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
    """Authenticate an account and return a short-lived access token."""
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

    return jsonify(
        access_token=issue_access_token(user.id),
        token_type="Bearer",
        expires_in=current_app.config["TOKEN_TTL_SECONDS"],
        user=user_payload(user),
    )


@auth_bp.get("/api/me")
@require_authenticated_api
def current_user(user: User):
    """Return the server-validated identity used by browser page initialization."""
    return jsonify(user=user_payload(user))


@auth_bp.post("/logout")
def logout():
    """Return compatibility success; clients discard stateless tokens locally."""
    return "", 204


@auth_bp.get("/materials")
def materials_page():
    """Render a public, data-free browser material workspace shell."""
    return render_template("materials.html")


@auth_bp.get("/login")
def login_page():
    """Render the public browser login page."""
    return render_template("login.html")


@auth_bp.get('/apps')
def apps_page():
    """Public shell; the Bearer client guards all application data."""
    return render_template('apps.html')
