"""Offline checks for delivered PDF, evidence and runtime source identity."""
import hashlib
import json
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[2]
evidence=root/'docs/verification'
for filename in ['platform-controlled.json','platform-live.json']:
    report=json.loads((evidence/filename).read_text())
    assert report['all_successful'], filename
    assert len(report['cases'])==10, filename
    assert all(case['http_status']==200 for case in report['cases'])
    assert all(report['tool_calls_observed'][kind]>=1 for kind in ['http_tool','mcp_tool'])
    for case in report['cases']:
        trace=case['run']['trace']
        if case['name']=='no_evidence':assert not trace['exchanges']
        if case['name'] in {'builtin_skill','uploaded_skill'}:
            assert len(trace['steps'])==2
            assert all(step['status']=='completed' for step in trace['steps'])
        assert 'Authorization' not in json.dumps(trace)
    for filename,expected in report['runtime_hashes'].items():
        assert hashlib.sha256((root/filename).read_bytes()).hexdigest()==expected,filename
smoke=json.loads((evidence/'platform-deployment.json').read_text())
assert smoke['all_checks_passed']
pdf=root/'docs/campusclaw-platform-verification.pdf'
assert pdf.stat().st_size>30000
text=subprocess.check_output(['pdftotext',str(pdf),'-']).decode()
for term in ['226','Skill','MCP','tools','知识库','2025-06-18']:
    assert term in text,term
assert len([page for page in text.split('\f') if page.strip()])>=8
print('PASS: PDF + 20 execution scenarios + live HTTP/MCP tools + deployment + source hashes')
