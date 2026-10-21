"""Read-only live deployment smoke; records statuses, never tokens or material text."""
import json
from pathlib import Path
import urllib.request
import urllib.error
import subprocess
from datetime import datetime,timezone

opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
checks=[]
def call(path,payload=None,token=None,expect=200):
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    req=urllib.request.Request('http://127.0.0.1:8000'+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
    try:
        with opener.open(req,timeout=20) as response:
            status=response.status;body=json.loads(response.read())
    except urllib.error.HTTPError as error:
        status=error.code;body=json.loads(error.read())
    checks.append({'path':path,'status':status,'expected':expect})
    return body
call('/health');call('/api/platform/apps',expect=401)
login=call('/login',{'account':'teacher-a','password':'teacher-a-password'})
token=login.get('access_token')
assert token
for path in ['/api/platform/apps','/api/platform/templates','/api/platform/skills','/api/platform/connectors','/api/platform/runs','/api/materials']:
    call(path,token=token)
raw=subprocess.check_output(['docker','compose','ps','--format','json']).decode()
try:
    services=json.loads(raw)
    if isinstance(services,dict):services=[services]
except json.JSONDecodeError:services=[json.loads(line) for line in raw.splitlines() if line.strip()]
health=[{'service':s['Service'],'state':s['State'],'health':s.get('Health')} for s in services]
assert {s['service'] for s in health}=={'campusclaw','mysql','qdrant','demo-tools'}
assert all(s['health']=='healthy' for s in health)
report={'services':health,'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'all_checks_passed':all(c['status']==c['expected'] for c in checks)}
Path(__file__).with_name('platform-deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
