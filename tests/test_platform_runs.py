import copy
import json
from dataclasses import replace
import pytest
from tests.test_platform_catalog import app,client_for
from tests.test_platform_connectors import remote,config,call_message
from campusclaw.platform_chat import PlatformChat
from campusclaw.platform_tools import configured_tools
from campusclaw.models import ApplicationRun,KnowledgeChunk,User
from campusclaw.knowledge_retrieval import RankedChunk
from campusclaw.ai_providers import ProviderUnavailable


def install_chat(app,answers):
    calls=[]
    settings=replace(app.config['GATEWAY_SETTINGS'],chat_base_url='https://synthetic/v1',chat_api_key='never-log-this')
    def transport(url,payload,*_):
        calls.append(copy.deepcopy(payload))
        message=answers.pop(0)
        if isinstance(message,Exception):raise message
        return {'choices':[{'message':message if isinstance(message,dict) else {'role':'assistant','content':message}}]}
    app.extensions['platform_chat']=PlatformChat(settings,transport)
    return calls


def submit(client,**kwargs):
    return client.post('/api/platform/runs',json={'app_id':'writing','input':'解释光合作用','audience':'小学生',**kwargs})


def test_app_instructions_and_rendered_template_are_sent(app):
    teacher=client_for(app)
    tid=teacher.post('/api/platform/templates',json={'name':'解释','content':'请向{{audience}}解释：{{input}}'}).json['template']['id']
    calls=install_chat(app,['答案甲','答案乙','答案丙'])
    for app_id in ['writing','study','exercises']:
        response=submit(teacher,app_id=app_id,template_id=tid)
        assert response.status_code==200
        record=teacher.get('/api/platform/runs/'+str(response.json['run_id'])).json
        assert record['trace']['rendered_template']=='请向小学生解释：解释光合作用'
        assert len(record['trace']['exchanges'])==1
        assert 'never-log-this' not in json.dumps(record)
    assert len({call['messages'][0]['content'] for call in calls})==3
    assert all('请向小学生解释' in call['messages'][1]['content'] for call in calls)


def test_builtin_and_uploaded_skills_use_full_manifest_and_previous_result(app):
    from tests.test_platform_skills import upload
    from campusclaw.platform_skills import BUILTIN_SKILLS
    client=client_for(app)
    skill=copy.deepcopy(BUILTIN_SKILLS['draft-review']);skill['instructions']='CUSTOM_MANIFEST_SENTINEL'
    uploaded=upload(client,skill).json['skill']['id']
    for skill_id in ['builtin:draft-review',uploaded]:
        calls=install_chat(app,['初稿','完成审校'])
        response=submit(client,skill_id=skill_id)
        assert response.status_code==200 and response.json['answer']=='完成审校'
        assert '初稿' in calls[1]['messages'][-1]['content']
        for call in calls:
            assert '完整Skill清单' in call['messages'][0]['content']
            assert ('CUSTOM_MANIFEST_SENTINEL' in call['messages'][0]['content']) == (skill_id==uploaded)
        trace=client.get('/api/platform/runs/'+str(response.json['run_id'])).json['trace']
        assert [step['status'] for step in trace['steps']]==['completed','completed']


def test_failed_skill_stops_and_records_private_error(app):
    calls=install_chat(app,[ProviderUnavailable('private key should not leak'),'should not execute'])
    client=client_for(app);response=submit(client,skill_id='builtin:draft-review')
    assert response.status_code==503 and len(calls)==1
    trace=client.get('/api/platform/runs/'+str(response.json['run_id'])).json
    assert trace['trace']['steps'][0]['status']=='failed'
    assert 'private key' not in json.dumps(trace)


def test_run_owner_and_current_class_are_enforced(app):
    install_chat(app,['answer']);client=client_for(app)
    run_id=submit(client).json['run_id'];path='/api/platform/runs/'+str(run_id)
    assert client_for(app,'student-a').get(path).status_code==404
    assert client_for(app,'teacher-b').get(path).status_code==404
    db=app.extensions['sqlalchemy']['session'];db.query(User).filter_by(account='teacher-a').one().class_id=2;db.commit()
    assert client.get(path).status_code==404
    assert client.get('/api/platform/runs').json['runs']==[]


def test_reject_cross_class_bindings_before_model(app):
    foreign=client_for(app,'teacher-b')
    tid=foreign.post('/api/platform/templates',json={'name':'secret','content':'private'}).json['template']['id']
    calls=install_chat(app,[])
    assert submit(client_for(app),template_id=tid).status_code==404
    assert submit(client_for(app),tools=['foreign__tool']).status_code==404
    assert calls==[]


@pytest.mark.parametrize('changes',[{'app_id':'unknown'},{'input':''},{'input':'x'*4001},{'use_knowledge':'yes'},{'tools':[{}]},{'template_id':True},{'template_id':2**100},{'skill_id':[]},{'skill_id':'uploaded:'+('9'*100)}])
def test_invalid_inputs_have_no_model_calls(app,changes):
    calls=install_chat(app,[])
    assert submit(client_for(app),**changes).status_code in {400,404}
    assert calls==[]


def test_knowledge_is_bounded_and_citations_are_checked(app,monkeypatch):
    db=app.extensions['sqlalchemy']['session'];chunk=db.query(KnowledgeChunk).filter_by(class_id=1).one()
    monkeypatch.setattr('campusclaw.platform_execution.hybrid_retrieve',lambda *a,**k:[RankedChunk(chunk)]*10)
    calls=install_chat(app,['缺少引用','材料的内容如上。[1]'])
    client=client_for(app);result=submit(client,use_knowledge=True)
    assert result.status_code==200 and len(result.json['citations'])==1
    assert len(calls)==2
    trace=client.get('/api/platform/runs/'+str(result.json['run_id'])).json['trace']
    assert len(trace['sources'])==1 and trace['citation_retry'] is True
    assert chunk.chunk_text in calls[0]['messages'][1]['content']
    assert 'Class B' not in json.dumps(trace)


def test_empty_knowledge_never_calls_chat_and_unbound_never_retrieves(app,monkeypatch):
    queries=[]
    monkeypatch.setattr('campusclaw.platform_execution.hybrid_retrieve',lambda *a,**k:queries.append(a[1]) or [])
    calls=install_chat(app,['unbound answer']);client=client_for(app)
    assert submit(client,use_knowledge=True).json['answer']=='资料中未找到相关内容'
    assert calls==[]
    assert submit(client).status_code==200 and len(queries)==1


def test_mcp_selected_tool_executes_and_is_captured(app,remote):
    base,log=remote
    app.config['PLATFORM_CONNECTORS']=configured_tools([config(base)])
    client=client_for(app)
    client.put('/api/platform/connectors/mcp',json={'enabled':True})
    name=client.get('/api/platform/tools').json['tools'][0]['definition']['function']['name']
    calls=install_chat(app,[call_message(name),'相加结果为5'])
    response=submit(client,tools=[name])
    assert response.status_code==200
    trace=client.get('/api/platform/runs/'+str(response.json['run_id'])).json['trace']
    assert trace['tools'][0]['result']['content'][0]['text']=='5'
    assert base not in json.dumps(trace)
    assert calls[1]['messages'][-1]['role']=='tool'
    assert any(item.get('payload',{}).get('method')=='tools/call' for item in log)


def test_unsupported_final_citations_fail(app,monkeypatch):
    chunk=app.extensions['sqlalchemy']['session'].query(KnowledgeChunk).filter_by(class_id=1).one()
    monkeypatch.setattr('campusclaw.platform_execution.hybrid_retrieve',lambda *a,**k:[RankedChunk(chunk)])
    calls=install_chat(app,['wrong [99]','still wrong [99]'])
    response=submit(client_for(app),use_knowledge=True)
    assert response.status_code==503 and len(calls)==2
