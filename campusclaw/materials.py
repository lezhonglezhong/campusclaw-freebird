"""Class-scoped material read endpoints."""

from flask import Blueprint, current_app, jsonify

from campusclaw.auth import require_authenticated_api
from campusclaw.models import Material, User


materials_bp = Blueprint("materials", __name__, url_prefix="/api/materials")


def material_payload(material: Material) -> dict[str, int | str]:
    return {
        "id": material.id,
        "display_name": material.display_name,
        "class_id": material.class_id,
        "uploader_id": material.uploader_id,
        "status": material.status,
    }


@materials_bp.get("")
@require_authenticated_api
def list_materials(user: User):
    db_session = current_app.extensions["sqlalchemy"]["session"]
    materials = db_session.query(Material).filter_by(class_id=user.class_id).order_by(Material.id).all()
    return jsonify(materials=[material_payload(material) for material in materials])


@materials_bp.get("/<int:material_id>")
@require_authenticated_api
def material_detail(user: User, material_id: int):
    db_session = current_app.extensions["sqlalchemy"]["session"]
    material = db_session.query(Material).filter_by(id=material_id, class_id=user.class_id).one_or_none()
    if material is None:
        return jsonify(error="not_found"), 404
    return jsonify(material=material_payload(material))
