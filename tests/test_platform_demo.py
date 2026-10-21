import pytest
from campusclaw.demo_tools import app, demo_connectors
from campusclaw.platform_tools import configured_tools


def test_demo_http_calculator_and_origin_protection():
    client=app.test_client()
    assert client.post('/calculate',json={'a':6,'b':7,'operation':'multiply'}).json=={'result':42}
    assert client.post('/calculate',json={'a':6,'b':0,'operation':'divide'}).status_code==400
    assert client.post('/calculate',json={'a':6,'b':7,'operation':'multiply'},headers={'Origin':'https://evil.example'}).status_code==403
    assert len(configured_tools(demo_connectors('http://demo:8010')))==2


def test_demo_mcp_protocol_and_failed_tool():
    client=app.test_client();headers={'MCP-Protocol-Version':'2025-06-18'}
    init=client.post('/mcp',json={'jsonrpc':'2.0','id':1,'method':'initialize','params':{}})
    assert init.json['result']['capabilities']=={'tools':{}}
    assert client.post('/mcp',json={'jsonrpc':'2.0','method':'notifications/initialized'},headers=headers).status_code==202
    assert client.post('/mcp',json={'jsonrpc':'2.0','id':2,'method':'tools/list'},headers=headers).json['result']['tools'][0]['name']=='calculate'
    response=client.post('/mcp',json={'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'calculate','arguments':{'a':1,'b':0,'operation':'divide'}}},headers=headers)
    assert response.json['result']['isError'] is True
    assert client.get('/mcp').status_code==405
