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


@platform_bp.get('/skills')
@require_authenticated_api
def skills(user):
    import json
    from campusclaw.models import UploadedSkill
    from campusclaw.platform_skills import BUILTIN_SKILLS
    items = [{'id': 'builtin:'+key, 'builtin': True, 'manifest': manifest}
             for key, manifest in BUILTIN_SKILLS.items()]
    items.extend({'id': 'uploaded:'+str(item.id), 'builtin': False, 'manifest': json.loads(item.manifest)}
                 for item in session().query(UploadedSkill).filter_by(class_id=user.class_id).order_by(UploadedSkill.id))
    return jsonify(skills=items)


@platform_bp.post('/skills')
@require_teacher
def upload_skill(user):
    import json
    from campusclaw.models import UploadedSkill
    from campusclaw.platform_skills import MAX_SKILL_BYTES, parse_skill
    from werkzeug.exceptions import RequestEntityTooLarge
    request.max_content_length = 64 * 1024
    try:
        uploaded = request.files.get('file')
        if uploaded is None or not (uploaded.filename or '').lower().endswith('.json'):
            raise ValueError()
        manifest = parse_skill(uploaded.read(MAX_SKILL_BYTES + 1))
    except (ValueError, RequestEntityTooLarge):
        return jsonify(error='invalid_skill'), 400
    item = UploadedSkill(class_id=user.class_id, manifest=json.dumps(manifest, ensure_ascii=False))
    session().add(item)
    session().commit()
    return jsonify(skill={'id': 'uploaded:'+str(item.id), 'builtin': False, 'manifest': manifest}), 201


@platform_bp.delete('/skills/<int:item_id>')
@require_teacher
def delete_skill(user, item_id):
    from campusclaw.models import UploadedSkill
    item = session().query(UploadedSkill).filter_by(id=item_id, class_id=user.class_id).one_or_none()
    if item is None: return jsonify(error='not_found'), 404
    session().delete(item)
    session().commit()
    return '', 204
