import json
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from tests.test_platform_catalog import app, client_for
from campusclaw.platform_tools import MCPClient, ToolRegistry, ToolUnavailable, configured_tools, request_json, validate_schema
from campusclaw.platform_chat import PlatformChat, generate_with_tools

SCHEMA = {'type':'object','properties':{'a':{'type':'number'},'b':{'type':'number'}},'required':['a','b'],'additionalProperties':False}


@pytest.fixture
def remote():
    log = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_): pass
        def do_DELETE(self):
            log.append({'delete': True, 'session': self.headers.get('Mcp-Session-Id')})
            self.send_response(200);self.end_headers();self.wfile.write(b'{}')
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            log.append({'path':self.path,'payload':payload,'headers':dict(self.headers)})
            if self.path == '/redirect':
                self.send_response(302);self.send_header('Location','/http');self.end_headers();return
            if self.path == '/http':
                response = {'sum':payload['a']+payload['b']}
            else:
                method = payload['method']
                if method == 'notifications/initialized':
                    self.send_response(202);self.end_headers();return
                if method == 'initialize':
                    result = {'protocolVersion':'2025-06-18','capabilities':{'tools':{}}}
                elif method == 'tools/list':
                    if 'cursor' not in payload['params']: result = {'tools':[],'nextCursor':'page2'}
                    else: result = {'tools':[{'name':'sum','description':'相加','inputSchema':SCHEMA}]}
                else:
                    args = payload['params']['arguments']
                    result = {'content':[{'type':'text','text':str(args['a']+args['b'])}]}
                response = {'jsonrpc':'2.0','id':payload['id'],'result':result}
            self.send_response(200)
            if payload.get('method') == 'initialize': self.send_header('Mcp-Session-Id','test-session')
            sse = self.path == '/sse'
            self.send_header('Content-Type','text/event-stream' if sse else 'application/json');self.end_headers()
            raw = json.dumps(response).encode()
            self.wfile.write(b': heartbeat\n\ndata: '+raw+b'\n\n' if sse else raw)
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}',log
    server.shutdown();server.server_close();thread.join()


def config(base,kind='mcp',path='/mcp'):
    return {'id':kind,'type':kind,'label':'测试工具','url':base+path, 'input_schema':SCHEMA}


@pytest.mark.parametrize('path',['/mcp','/sse'])
def test_real_http_mcp_handshake_pagination_session_and_call(remote,path):
    base,log = remote
    registry = ToolRegistry([config(base,path=path)])
    name = next(iter(registry.entries))
    assert registry.call(name,{'a':2,'b':3})['content'][0]['text'] == '5'
    assert [x['payload']['method'] for x in log] == ['initialize','notifications/initialized','tools/list','tools/list','tools/call']
    assert log[-1]['headers']['Mcp-Session-Id'] == 'test-session'
    assert log[-1]['headers']['Mcp-Protocol-Version'] == '2025-06-18'
    assert 'text/event-stream' in log[-1]['headers']['Accept']
    registry.close()
    assert log[-1] == {'delete':True,'session':'test-session'}


def test_http_tool_schema_and_redirect_safety(remote):
    base,log=remote
    registry=ToolRegistry([config(base,'http','/http')]);name=next(iter(registry.entries))
    assert registry.call(name,{'a':3,'b':4}) == {'sum':7}
    with pytest.raises(ToolUnavailable): registry.call(name,{'a':'bad','b':4})
    assert len(log)==1
    with pytest.raises(ToolUnavailable): request_json(config(base,'http','/redirect'),{'a':1,'b':2})
    assert len(log)==2


@pytest.mark.parametrize('response', [
    {'jsonrpc':'2.0','id':999,'result':{}},
    {'jsonrpc':'2.0','id':1,'error':{'message':'private'}},
    {'jsonrpc':'2.0','id':1,'result':{'protocolVersion':'future','capabilities':{'tools':{}}}},
])
def test_bad_mcp_responses_fail(response):
    client=MCPClient(config('http://localhost'),lambda *a,**k:(response,{}))
    with pytest.raises(ToolUnavailable):client.discover()


def test_schema_remote_references_are_not_resolved():
    with pytest.raises(ToolUnavailable):validate_schema({'type':'object','properties':{'x':{'$ref':'http://private/schema'}}})
    with pytest.raises(RuntimeError):configured_tools('[{"id":"bad","type":"http","url":"file:///etc/passwd"}]')


def test_class_enablement_hides_configuration_secrets(app,remote):
    base,_=remote
    cfg=config(base,'http','/http');cfg['token_env']='EXTERNAL_SECRET'
    app.config['PLATFORM_CONNECTORS']=configured_tools([cfg])
    teacher=client_for(app);student=client_for(app,'student-a');foreign=client_for(app,'teacher-b')
    assert student.get('/api/platform/connectors').json['connectors']==[]
    assert student.put('/api/platform/connectors/http',json={'enabled':True}).status_code==403
    assert teacher.put('/api/platform/connectors/http',json={'enabled':True}).status_code==200
    assert foreign.get('/api/platform/connectors').json['connectors'][0]['enabled'] is False
    result=student.get('/api/platform/tools')
    assert len(result.json['tools'])==1
    assert base not in result.text and 'EXTERNAL_SECRET' not in result.text


def chat_for(app,responses,observed):
    settings=replace(app.config['GATEWAY_SETTINGS'],chat_base_url='https://synthetic/v1',chat_api_key='synthetic-key')
    def transport(url,payload,key,timeout):
        observed.append(payload)
        return {'choices':[{'message':responses.pop(0)}]}
    return PlatformChat(settings,transport)


def call_message(name,arguments='{"a":2,"b":3}',call_id='call-1'):
    return {'role':'assistant','content':None,'tool_calls':[{'id':call_id,'type':'function','function':{'name':name,'arguments':arguments}}]}


def test_model_function_definition_execution_and_result_roundtrip(app,remote):
    base,_=remote;registry=ToolRegistry([config(base,'http','/http')]);name=next(iter(registry.entries))
    observed=[];chat=chat_for(app,[call_message(name),{'role':'assistant','content':'结果为5'}],observed)
    trace={'exchanges':[],'tools':[]}
    result=generate_with_tools(chat,[{'role':'user','content':'2+3'}],registry,[name],trace,{'calls':0,'ids':set()})
    assert result=='结果为5'
    assert observed[0]['tool_choice']=='auto' and observed[0]['tools'][0]['function']['parameters']==SCHEMA
    assert observed[1]['messages'][-1]=={'role':'tool','tool_call_id':'call-1','content':'{"sum": 5}'}
    assert trace['tools'][0]['status']=='completed' and len(trace['exchanges'])==2
    assert 'synthetic-key' not in json.dumps(trace)


@pytest.mark.parametrize('kind',['unknown','schema','json','duplicate','loop'])
def test_invalid_or_looping_model_cannot_execute_arbitrarily(app,remote,kind):
    base,log=remote;registry=ToolRegistry([config(base,'http','/http')]);name=next(iter(registry.entries))
    message=call_message(name)
    if kind=='unknown':message=call_message('not-allowed')
    if kind=='schema':message=call_message(name,'{"a":"bad","b":3}')
    if kind=='json':message=call_message(name,'invalid-json')
    if kind=='duplicate':message['tool_calls']*=2
    responses=[message] if kind!='loop' else [call_message(name,call_id='call-'+str(i)) for i in range(3)]
    trace={'exchanges':[],'tools':[]}
    with pytest.raises(ToolUnavailable):generate_with_tools(chat_for(app,responses,[]),[],registry,[name],trace,{'calls':0,'ids':set()})
    assert len(log)==(3 if kind=='loop' else 0)


def test_budget_shared_between_skill_steps(app,remote):
    base,log=remote;registry=ToolRegistry([config(base,'http','/http')]);name=next(iter(registry.entries))
    with pytest.raises(ToolUnavailable):
        generate_with_tools(chat_for(app,[call_message(name)],[]),[],registry,[name],{'exchanges':[],'tools':[]},{'calls':4,'ids':set()})
    assert log==[]


def test_mcp_error_result_does_not_become_success():
    def transport(cfg,payload,*args,**kwargs):
        return {'jsonrpc':'2.0','id':payload['id'],'result':{'isError':True,'content':[{'type':'text','text':'failed'}]}},{}
    client=MCPClient(config('http://localhost'),transport)
    with pytest.raises(ToolUnavailable,match='tool_execution_failed'):client.call('sum',{})


def test_repeated_pagination_cursor_is_rejected():
    def transport(cfg,payload,*args,**kwargs):
        if payload['method']=='notifications/initialized':return {},{}
        result=({'protocolVersion':'2025-06-18','capabilities':{'tools':{}}} if payload['method']=='initialize'
                else {'tools':[],'nextCursor':'again'})
        return {'jsonrpc':'2.0','id':payload['id'],'result':result},{}
    with pytest.raises(ToolUnavailable,match='invalid_cursor'):MCPClient(config('http://localhost'),transport).discover()
