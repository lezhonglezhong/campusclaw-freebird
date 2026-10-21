"""Capture isolated platform executions using synthetic data, optionally real chat.

Run from repository root. JSON goes to stdout. --live uses existing server-side
model settings and PLATFORM_DEMO_TOOLS_URL, but never production DB/materials.
"""
import argparse
import contextlib
import copy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from werkzeug.serving import make_server
from campusclaw import create_app
from campusclaw.seed import seed_data
from campusclaw.demo_tools import app as demo_app, demo_connectors
from campusclaw.models import KnowledgeChunk
from campusclaw.platform_chat import PlatformChat
from campusclaw.platform_tools import configured_tools
from campusclaw.platform_skills import BUILTIN_SKILLS


def capture(live=False, case_names=None):
    servers=[]
    wire=[]
    if not live:
        demo=make_server('127.0.0.1',0,demo_app,threaded=True)
        threading.Thread(target=demo.serve_forever,daemon=True).start();servers.append(demo)
        demo_url=f'http://127.0.0.1:{demo.server_port}'
        class Gateway(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_POST(self):
                payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                messages=payload['messages']
                if payload.get('tools') and messages[-1]['role']!='tool':
                    message={'role':'assistant','content':None,'tool_calls':[{'id':'sample-'+str(len(wire)),'type':'function',
                        'function':{'name':payload['tools'][0]['function']['name'],'arguments':'{"a":13,"b":17,"operation":"multiply"}'}}]}
                else:
                    answer=('光合作用需要阳光。[1]' if any('Sources:' in m.get('content','') for m in messages if isinstance(m.get('content'),str))
                            else '计算结果为221。' if messages[-1]['role']=='tool' else '已完成合成示例内容。')
                    message={'role':'assistant','content':answer}
                response={'choices':[{'message':message}],'model':payload['model']}
                wire.append({'path':self.path,'request':payload,'response':response})
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
                self.wfile.write(json.dumps(response,ensure_ascii=False).encode())
        gateway=ThreadingHTTPServer(('127.0.0.1',0),Gateway)
        threading.Thread(target=gateway.serve_forever,daemon=True).start();servers.append(gateway)
    else:
        import os
        demo_url=os.environ.get('PLATFORM_DEMO_TOOLS_URL','http://demo-tools:8010')
    report={'kind':'live-model-isolated-synthetic-data' if live else 'controlled-http-model-with-real-http-mcp-tools',
            'utc':datetime.now(timezone.utc).isoformat(),'cases':[], 'runtime_hashes':{}}
    for path in Path('campusclaw').rglob('*'):
        if path.is_file() and path.suffix in {'.py','.js','.html','.css','.json'}:
            report['runtime_hashes'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        with tempfile.TemporaryDirectory(prefix='platform-evidence-') as tmp:
            app=create_app({'TESTING':True,'DATABASE_URL':f'sqlite:///{tmp}/audit.db',
                'MATERIAL_STORAGE_DIR':tmp+'/materials','TOKEN_SIGNING_SECRET':'isolated-audit-secret-for-synthetic-data-only',
                'PLATFORM_CONNECTORS_JSON':demo_connectors(demo_url)})
            class Embedding:
                def embed(self,texts):return [[0.0]*2048 for _ in texts]
            class Store:
                points=[]
                def ensure_collection(self):pass
                def upsert(self,points):pass
                def search(self,*_):return self.points
            store=Store()
            app.extensions['embedding_provider']=Embedding();app.extensions['vector_store']=store
            seed_data(app)
            if not live:
                settings=replace(app.config['GATEWAY_SETTINGS'],chat_base_url=f'http://127.0.0.1:{gateway.server_port}/v1',
                                 chat_api_key='synthetic-key',chat_model='course-chat')
                app.extensions['platform_chat']=PlatformChat(settings)
            client=app.test_client()
            token=client.post('/login',json={'account':'teacher-a','password':'teacher-a-password'}).json['access_token']
            client.environ_base['HTTP_AUTHORIZATION']='Bearer '+token
            template=client.post('/api/platform/templates',json={'name':'面向初学者','content':'面向{{audience}}清楚地说明：{{input}}'}).json['template']
            skill=copy.deepcopy(BUILTIN_SKILLS['draft-review']);skill['name']='审计上传技能'
            uploaded=client.post('/api/platform/skills',data={'file':(io.BytesIO(json.dumps(skill,ensure_ascii=False).encode()),'audit.json')}).json['skill']
            material=client.post('/api/materials',json={'display_name':'审计光合作用资料','content':'光合作用需要阳光。'}).json['material']
            db=app.extensions['sqlalchemy']['session'];chunk=db.query(KnowledgeChunk).filter_by(material_id=material['id']).one()
            store.points=[{'id':chunk.id,'score':0.95}]
            for cid in ['demo-http','demo-mcp']:
                assert client.put('/api/platform/connectors/'+cid,json={'enabled':True}).status_code==200
            discovered=client.get('/api/platform/tools').json
            assert not discovered['errors'],discovered['errors']
            names={item['connector_id']:item['definition']['function']['name'] for item in discovered['tools']}
            report['discovered_tools']=discovered['tools']
            cases=[
                ('writing',{'app_id':'writing','input':'今天学习了新知识，我很开心。'}),
                ('study',{'app_id':'study','input':'请给我一个学习分数加法的一天计划。'}),
                ('exercises',{'app_id':'exercises','input':'小学分数加法'}),
                ('template',{'app_id':'writing','input':'太阳照耀校园。','audience':'初学者','template_id':template['id']}),
                ('builtin_skill',{'app_id':'writing','input':'请润色：我喜欢学习。','skill_id':'builtin:draft-review'}),
                ('uploaded_skill',{'app_id':'writing','input':'请润色：校园非常美丽。','skill_id':uploaded['id'],'template_id':template['id']}),
                ('knowledge',{'app_id':'writing','input':'仅复述审计光合作用资料中关于光合作用的事实，用一句话回答。','use_knowledge':True}),
                ('http_tool',{'app_id':'writing','input':'必须调用所选的计算器工具，计算13乘17。依据工具结果回答。','tools':[names['demo-http']]}),
                ('mcp_tool',{'app_id':'writing','input':'必须调用所选的计算器工具，计算13乘17。依据工具结果回答。','tools':[names['demo-mcp']]})]
            for name,payload in cases:
                if case_names and name not in case_names: continue
                response=client.post('/api/platform/runs',json=payload)
                record={'name':name,'client_request':payload,'http_status':response.status_code,'api_response':response.json}
                if response.json.get('run_id'):
                    record['run']=client.get('/api/platform/runs/'+str(response.json['run_id'])).json
                report['cases'].append(record)
            store.points=[]
            payload={'app_id':'writing','input':'zqxv_no_matching_audit_phrase','use_knowledge':True}
            response=client.post('/api/platform/runs',json=payload)
            report['cases'].append({'name':'no_evidence','client_request':payload,'http_status':response.status_code,
                'api_response':response.json,'run':client.get('/api/platform/runs/'+str(response.json['run_id'])).json})
            report['all_successful']=all(case['http_status']==200 for case in report['cases'])
            report['tool_calls_observed']={case['name']:len(case['run']['trace']['tools']) for case in report['cases'] if case['name'].endswith('_tool')}
            db.remove();app.extensions['sqlalchemy']['engine'].dispose()
    finally:
        for server in servers:server.shutdown();server.server_close()
    if not live:report['wire_exchanges']=wire
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--case',action='append');args=parser.parse_args()
    print(json.dumps(capture(args.live,args.case),ensure_ascii=False,indent=2))
