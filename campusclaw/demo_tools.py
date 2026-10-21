"""Read-only demonstration HTTP/MCP service; no database or gateway credentials."""
import math
from flask import Flask, jsonify, request
from jsonschema import Draft202012Validator, ValidationError

app = Flask('campusclaw_demo_tools')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
CALCULATOR_SCHEMA = {
    'type':'object','properties':{'a':{'type':'number'},'b':{'type':'number'},
        'operation':{'type':'string','enum':['add','subtract','multiply','divide']}},
    'required':['a','b','operation'],'additionalProperties':False,
}


def demo_connectors(base):
    return [
        {'id':'demo-http','type':'http','label':'演示计算器','url':base.rstrip('/')+'/calculate','input_schema':CALCULATOR_SCHEMA},
        {'id':'demo-mcp','type':'mcp','label':'演示 MCP 计算器','url':base.rstrip('/')+'/mcp'},
    ]


def calculate(arguments):
    Draft202012Validator(CALCULATOR_SCHEMA).validate(arguments)
    a,b,op = arguments['a'],arguments['b'],arguments['operation']
    if not math.isfinite(a) or not math.isfinite(b):raise ValueError()
    if op=='add':value=a+b
    elif op=='subtract':value=a-b
    elif op=='multiply':value=a*b
    else:value=a/b
    if not math.isfinite(value):raise ValueError()
    return {'result':value}


@app.before_request
def reject_browser_origins():
    if request.headers.get('Origin'):return jsonify(error='origin_not_allowed'),403


@app.get('/health')
def health():return jsonify(status='ok')


@app.post('/calculate')
def http_calculate():
    try:return jsonify(calculate(request.get_json(silent=True)))
    except (ValidationError, ValueError, TypeError, ZeroDivisionError, OverflowError):return jsonify(error='invalid_arguments'),400


@app.route('/mcp',methods=['POST','DELETE'])
def mcp():
    if request.method=='DELETE':return jsonify(ok=True)
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict) or payload.get('jsonrpc')!='2.0':return jsonify(error='invalid_request'),400
    method=payload.get('method');params=payload.get('params',{});request_id=payload.get('id')
    if method=='initialize':
        result={'protocolVersion':'2025-06-18','capabilities':{'tools':{}},'serverInfo':{'name':'campusclaw-demo','version':'1.0'}}
    else:
        if request.headers.get('MCP-Protocol-Version')!='2025-06-18':return jsonify(error='unsupported_protocol'),400
        if method=='notifications/initialized':return '',202
        if method=='tools/list':
            result={'tools':[{'name':'calculate','description':'对两个数字进行加、减、乘、除运算（只读计算器）','inputSchema':CALCULATOR_SCHEMA}]}
        elif method=='tools/call':
            try:
                if not isinstance(params,dict) or params.get('name')!='calculate':raise ValueError()
                value=calculate(params.get('arguments'))
                result={'content':[{'type':'text','text':str(value['result'])}],'structuredContent':value,'isError':False}
            except (ValidationError, ValueError, TypeError, ZeroDivisionError, OverflowError):
                result={'content':[{'type':'text','text':'参数错误或不能除以零'}],'isError':True}
        else:return jsonify(jsonrpc='2.0',id=request_id,error={'code':-32601,'message':'Method not found'})
    return jsonify(jsonrpc='2.0',id=request_id,result=result)


if __name__=='__main__':app.run(host='0.0.0.0',port=8010)
