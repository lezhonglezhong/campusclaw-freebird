"""Reproduce an isolated HTTP-boundary audit; no real credentials or data used.

Run from repo root: PYTHONDONTWRITEBYTECODE=1 python docs/verification/capture_requests.py
"""
import json
import sys
import tempfile
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from campusclaw import create_app
from campusclaw.ai_providers import OpenAIChatProvider, OpenAIEmbeddingProvider
from campusclaw.models import KnowledgeChunk
from campusclaw.seed import seed_data

calls = []
chat_answers = []


class Gateway(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path.endswith('/embeddings'):
            response = {'data': [{'index': 0, 'embedding': [0.0] * 2048}]}
        else:
            response = {'choices': [{'message': {'role': 'assistant', 'content': chat_answers.pop(0)}}]}
        calls.append({'method': 'POST', 'path': self.path,
                      'headers': {'Content-Type': self.headers['Content-Type'],
                                  'Authorization': 'Bearer <synthetic-audit-key>'},
                      'request': body, 'response': response})
        raw = json.dumps(response, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(raw)


server = HTTPServer(('127.0.0.1', 0), Gateway)
threading.Thread(target=server.serve_forever, daemon=True).start()
report = {'kind': 'controlled-local-http-not-live-model', 'cases': []}
try:
    with tempfile.TemporaryDirectory(prefix='campusclaw-audit-') as directory:
        app = create_app({'TESTING': True, 'DATABASE_URL': f'sqlite:///{directory}/audit.db',
                          'MATERIAL_STORAGE_DIR': f'{directory}/materials',
                          'TOKEN_SIGNING_SECRET': 'synthetic-audit-signing-secret'})
        settings = replace(app.config['GATEWAY_SETTINGS'],
                           embedding_base_url=f'http://127.0.0.1:{server.server_port}/v1',
                           chat_base_url=f'http://127.0.0.1:{server.server_port}/v1',
                           embedding_api_key='synthetic-audit-key', chat_api_key='synthetic-audit-key',
                           embedding_model='course-embedding', chat_model='course-chat')
        # Seeding must not contact an environment-provided external service.
        class Store:
            points = []
            def ensure_collection(self): pass
            def upsert(self, points): pass
            def search(self, vector, class_id, limit):
                assert len(vector) == 2048 and class_id == 1 and limit == 12
                return self.points
        store = Store()
        app.extensions['vector_store'] = store
        app.extensions['embedding_provider'] = OpenAIEmbeddingProvider(settings)
        app.extensions['chat_provider'] = OpenAIChatProvider(settings)
        seed_data(app)
        session = app.extensions['sqlalchemy']['session']
        own = session.query(KnowledgeChunk).filter_by(class_id=1).one()
        foreign = session.query(KnowledgeChunk).filter_by(class_id=2).one()
        report['fixture'] = {'own_text': own.chunk_text, 'foreign_text': foreign.chunk_text}
        store.points = [{'id': own.id, 'score': 0.9}, {'id': foreign.id, 'score': 0.99}]
        client = app.test_client()
        token = client.post('/login', json={'account': 'student-a', 'password': 'student-a-password'}).json['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        def run(name, payload, answers):
            calls.clear()
            chat_answers[:] = answers
            response = client.post('/api/ask', json=payload, headers=headers)
            record = {'name': name, 'client_request': payload, 'gateway_calls': list(calls),
                      'api_status': response.status_code, 'api_response': response.json}
            report['cases'].append(record)
            return record

        normal = run('bounded_history_and_ignored_client_overrides', {
            'question': 'A班资料的内容是什么', 'class_id': 2, 'model': 'client-model',
            'prompt': 'CLIENT_PROMPT_SENTINEL', 'skill': 'CLIENT_SKILL_SENTINEL',
            'tools': [{'name': 'CLIENT_TOOL_SENTINEL'}],
            'history': [{'role': 'system', 'content': 'CLIENT_SYSTEM_SENTINEL'}] +
                       [{'role': 'user', 'content': f'历史问题{i}'} for i in range(8)]
        }, ['资料内容已提供。[1]'])
        assert normal['api_status'] == 200
        payload = normal['gateway_calls'][-1]['request']
        assert set(payload) == {'model', 'messages'}
        assert len(payload['messages']) == 8
        wire = json.dumps(payload, ensure_ascii=False)
        assert 'CLIENT_' not in wire and foreign.chunk_text not in payload['messages'][-1]['content']
        assert own.chunk_text in payload['messages'][-1]['content']
        retry = run('citation_retry', {'question': 'A班资料的内容是什么'}, ['没有引用', '资料内容已提供。[1]'])
        assert len(retry['gateway_calls']) == 3 and retry['api_status'] == 200
        assert retry['gateway_calls'][1]['request']['messages'][-1] == retry['gateway_calls'][2]['request']['messages'][-1]
        invalid = run('retry_exhausted', {'question': 'A班资料的内容是什么'}, ['没有引用', '还是没有引用'])
        assert invalid['api_status'] == 503 and len(invalid['gateway_calls']) == 3
        store.points = []
        empty = run('no_evidence', {'question': 'UNMATCHED_AUDIT_SENTINEL'}, [])
        assert empty['api_status'] == 200 and len(empty['gateway_calls']) == 1
        assert empty['api_response']['citations'] == []
        report['routes'] = sorted(f'{sorted(rule.methods - {"HEAD", "OPTIONS"})} {rule.rule}' for rule in app.url_map.iter_rules())
        report['assertions'] = 'passed'
        session.remove()
        app.extensions['sqlalchemy']['engine'].dispose()
finally:
    server.shutdown()
target = Path(__file__).with_name('controlled-requests.json')
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(f'PASS: 4 controlled HTTP scenarios; evidence: {target}')
