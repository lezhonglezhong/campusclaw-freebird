"""Bearer-authenticated platform resources with class-scoped teacher management."""
from flask import Blueprint, current_app, jsonify, request
from campusclaw.auth import require_authenticated_api, require_teacher
from campusclaw.models import PromptTemplate
from campusclaw.platform_catalog import APPLICATIONS, DEFAULT_TEMPLATE, text_field, validate_template

platform_bp = Blueprint('platform', __name__, url_prefix='/api/platform')


def session():
    return current_app.extensions['sqlalchemy']['session']


def template_payload(item):
    return {'id': item.id, 'name': item.name, 'content': item.content}


@platform_bp.get('/apps')
@require_authenticated_api
def apps(user):
    return jsonify(apps=list(APPLICATIONS.values()), default_template=DEFAULT_TEMPLATE,
                   knowledge_url='/materials')


@platform_bp.get('/templates')
@require_authenticated_api
def templates(user):
    return jsonify(templates=[template_payload(item) for item in
        session().query(PromptTemplate).filter_by(class_id=user.class_id).order_by(PromptTemplate.id)])


@platform_bp.post('/templates')
@require_teacher
def create_template(user):
    payload = request.get_json(silent=True)
    try:
        if not isinstance(payload, dict): raise ValueError()
        name = text_field(payload.get('name'), 120)
        content = validate_template(payload.get('content'))
    except ValueError:
        return jsonify(error='invalid_template'), 400
    item = PromptTemplate(class_id=user.class_id, name=name, content=content)
    session().add(item)
    session().commit()
    return jsonify(template=template_payload(item)), 201


@platform_bp.put('/templates/<int:item_id>')
@require_teacher
def edit_template(user, item_id):
    item = session().query(PromptTemplate).filter_by(id=item_id, class_id=user.class_id).one_or_none()
    if item is None: return jsonify(error='not_found'), 404
    payload = request.get_json(silent=True)
    try:
        if not isinstance(payload, dict): raise ValueError()
        name = text_field(payload.get('name'), 120)
        content = validate_template(payload.get('content'))
    except ValueError:
        return jsonify(error='invalid_template'), 400
    item.name, item.content = name, content
    session().commit()
    return jsonify(template=template_payload(item))


@platform_bp.delete('/templates/<int:item_id>')
@require_teacher
def delete_template(user, item_id):
    item = session().query(PromptTemplate).filter_by(id=item_id, class_id=user.class_id).one_or_none()
    if item is None: return jsonify(error='not_found'), 404
    session().delete(item)
    session().commit()
    return '', 204
