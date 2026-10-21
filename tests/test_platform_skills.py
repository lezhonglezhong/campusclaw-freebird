import copy
import io
import json
import pytest
from tests.test_platform_catalog import app, client_for
from campusclaw.platform_skills import BUILTIN_SKILLS, execute_skill, parse_skill


def upload(client, manifest, name='skill.json'):
    raw = json.dumps(manifest, ensure_ascii=False).encode() if isinstance(manifest, dict) else manifest
    return client.post('/api/platform/skills', data={'file': (io.BytesIO(raw), name)})


def test_builtin_and_uploaded_skill_lifecycle(app):
    teacher, student, foreign = (client_for(app, name) for name in ['teacher-a','student-a','teacher-b'])
    manifest = copy.deepcopy(BUILTIN_SKILLS['draft-review'])
    assert len(student.get('/api/platform/skills').json['skills']) == 2
    assert upload(student, manifest).status_code == 403
    response = upload(teacher, manifest)
    assert response.status_code == 201
    assert student.get('/api/platform/skills').json['skills'][-1]['manifest'] == manifest
    assert len(foreign.get('/api/platform/skills').json['skills']) == 2
    item_id = response.json['skill']['id'].split(':')[1]
    assert foreign.delete('/api/platform/skills/'+item_id).status_code == 404
    assert teacher.delete('/api/platform/skills/'+item_id).status_code == 204


@pytest.mark.parametrize('raw,name', [(b'not json','x.json'),(b'{}','x.py'),(b'x'*16385,'x.json'),(b'x'*70000,'x.json'),(b'\xff','x.json'),(b'{"version":1,"version":1}','x.json')])
def test_reject_bad_upload(app, raw, name):
    assert upload(client_for(app), raw, name).status_code == 400


def test_reject_code_and_unknown_fields():
    manifest = copy.deepcopy(BUILTIN_SKILLS['draft-review'])
    manifest['steps'][0]['command'] = 'rm -rf anything'
    with pytest.raises(ValueError): parse_skill(json.dumps(manifest).encode())
    manifest = copy.deepcopy(BUILTIN_SKILLS['draft-review']);manifest['version'] = True
    with pytest.raises(ValueError): parse_skill(json.dumps(manifest).encode())


def test_execute_in_order_with_complete_manifest_and_previous_output():
    events, calls = [], []
    manifest = BUILTIN_SKILLS['draft-review']
    def generate(instruction, previous, full):
        calls.append((instruction, previous, json.loads(full)))
        return 'draft' if not previous else 'reviewed'
    assert execute_skill(manifest, generate, events) == 'reviewed'
    assert calls[0][1] == '' and calls[1][1] == 'draft'
    assert all(call[2] == manifest for call in calls)
    assert [event['status'] for event in events] == ['completed','completed']


def test_failed_step_stops_workflow():
    events = []
    def broken(*_): raise RuntimeError('gateway failed')
    with pytest.raises(RuntimeError): execute_skill(BUILTIN_SKILLS['draft-review'], broken, events)
    assert len(events) == 1 and events[0]['status'] == 'failed'
