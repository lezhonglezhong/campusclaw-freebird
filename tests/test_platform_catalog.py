import pytest
from campusclaw import create_app
from campusclaw.seed import seed_data
from campusclaw.platform_catalog import render_template


@pytest.fixture
def app(tmp_path, monkeypatch):
    for key in ['EMBEDDING_API_KEY', 'CHAT_API_KEY', 'QDRANT_URL', 'PLATFORM_CONNECTORS_JSON']:
        monkeypatch.delenv(key, raising=False)
    app = create_app({'TESTING': True, 'DATABASE_URL': f'sqlite:///{tmp_path}/test.db',
                      'MATERIAL_STORAGE_DIR': str(tmp_path/'materials'), 'TOKEN_SIGNING_SECRET': 'test-secret'})
    seed_data(app)
    yield app
    app.extensions['sqlalchemy']['session'].remove()
    app.extensions['sqlalchemy']['engine'].dispose()


def client_for(app, account='teacher-a'):
    client = app.test_client()
    result = client.post('/login', json={'account': account, 'password': account+'-password'})
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer '+result.json['access_token']
    return client


def test_catalog_authentication_and_distinct_instructions(app):
    assert app.test_client().get('/api/platform/apps').status_code == 401
    result = client_for(app, 'student-a').get('/api/platform/apps').json
    assert len(result['apps']) == 3
    assert len({x['instruction'] for x in result['apps']}) == 3
    assert result['knowledge_url'] == '/materials'


def test_template_crud_and_class_isolation(app):
    teacher = client_for(app)
    student = client_for(app, 'student-a')
    foreign = client_for(app, 'teacher-b')
    payload = {'name': '课堂讲解', 'content': '面向{{audience}}解释{{input}}'}
    assert student.post('/api/platform/templates', json=payload).status_code == 403
    response = teacher.post('/api/platform/templates', json=payload)
    assert response.status_code == 201
    item_id = response.json['template']['id']
    assert student.get('/api/platform/templates').json['templates'][0]['name'] == '课堂讲解'
    assert foreign.get('/api/platform/templates').json['templates'] == []
    path = f'/api/platform/templates/{item_id}'
    assert foreign.put(path, json=payload).status_code == 404
    assert foreign.delete(path).status_code == 404
    assert teacher.put(path, json={'name': '更新', 'content': '{{input}}'}).status_code == 200
    assert teacher.delete(path).status_code == 204
    assert student.get('/api/platform/templates').json['templates'] == []


@pytest.mark.parametrize('content', ['{{system}}', '{{ input }}', '{{input', 'x'*8001, '', 5])
def test_reject_bad_templates(app, content):
    assert client_for(app).post('/api/platform/templates', json={'name': 'test', 'content': content}).status_code == 400


def test_render_is_single_pass_and_never_evaluates_code():
    assert render_template('{{input}} / {{audience}}', '{{audience}}', '学生') == '{{audience}} / 学生'
    assert render_template('plain', 'ignored', '学生') == 'plain'
