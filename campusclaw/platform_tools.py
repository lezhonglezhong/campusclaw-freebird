"""Deployment-approved HTTP and MCP tools. No model-controlled network addresses."""
import hashlib
import json
import os
import re
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import URLError, HTTPError
from jsonschema import Draft202012Validator, ValidationError, SchemaError

from campusclaw.ai_providers import ProviderUnavailable

MAX_TOOL_BYTES = 64 * 1024
PROTOCOL = '2025-06-18'


class ToolUnavailable(ProviderUnavailable):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def bounded_json(value, limit=MAX_TOOL_BYTES):
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, RecursionError) as exc:
        raise ToolUnavailable('invalid_tool_data') from exc
    if len(raw) > limit: raise ToolUnavailable('tool_data_too_large')
    return raw


def validate_schema(schema):
    if not isinstance(schema, dict) or schema.get('type') != 'object':
        raise ToolUnavailable('invalid_tool_schema')
    bounded_json(schema, 8192)
    # External references must never trigger network or local-file resolution.
    def check(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {'$ref', '$dynamicRef', '$recursiveRef'}:
                    raise ToolUnavailable('schema_references_unsupported')
                check(item)
        elif isinstance(value, list):
            for item in value: check(item)
    check(schema)
    try: Draft202012Validator.check_schema(schema)
    except (SchemaError, RecursionError) as exc: raise ToolUnavailable('invalid_tool_schema') from exc
    return schema


def configured_tools(raw):
    try:
        configs = json.loads(raw or '[]') if isinstance(raw, str) else raw
        if not isinstance(configs, list) or len(configs) > 12: raise ValueError()
        result = {}
        for entry in configs:
            if not isinstance(entry, dict): raise ValueError()
            key = entry.get('id', '')
            if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,19}', key) or key in result:
                raise ValueError()
            if entry.get('type') not in {'http', 'mcp'}: raise ValueError()
            url = urlsplit(entry.get('url', ''))
            if url.scheme not in {'http','https'} or not url.hostname or url.username or url.password or url.fragment:
                raise ValueError()
            if not isinstance(entry.get('label'), str) or not 1 <= len(entry['label']) <= 120: raise ValueError()
            if 'token_env' in entry and (not isinstance(entry['token_env'], str) or not re.fullmatch(r'[A-Z][A-Z0-9_]+', entry['token_env'])):
                raise ValueError()
            if entry['type'] == 'http': validate_schema(entry.get('input_schema'))
            result[key] = entry
        return result
    except (ValueError, TypeError, ToolUnavailable, RecursionError) as exc:
        raise RuntimeError('Invalid PLATFORM_CONNECTORS_JSON') from exc


def request_json(config, payload, headers=None, notification=False, method='POST'):
    """Accept bounded JSON or POST SSE; correlate JSON-RPC at the caller."""
    request_headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
    request_headers.update(headers or {})
    if config.get('token_env'):
        token = os.environ.get(config['token_env'])
        if not token: raise ToolUnavailable('tool_credentials_unavailable')
        request_headers['Authorization'] = 'Bearer '+token
    body = bounded_json(payload, 32 * 1024) if payload is not None else None
    req = Request(config['url'], data=body, headers=request_headers, method=method)
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=10) as response:
            response_headers = dict(response.headers.items())
            if notification:
                if response.status != 202: raise ToolUnavailable('invalid_notification_response')
                return {}, response_headers
            if response.headers.get_content_type() == 'text/event-stream':
                start, size, data = time.monotonic(), 0, []
                while True:
                    line = response.readline(MAX_TOOL_BYTES+1)
                    size += len(line)
                    if size > MAX_TOOL_BYTES or time.monotonic()-start > 15:
                        raise ToolUnavailable('tool_response_too_large')
                    if not line: raise ToolUnavailable('incomplete_tool_stream')
                    decoded = line.decode('utf-8').rstrip('\r\n')
                    if decoded.startswith('data:'): data.append(decoded[5:].lstrip(' '))
                    elif not decoded and data:
                        value = json.loads('\n'.join(data));data = []
                        if isinstance(value, dict) and value.get('id') == payload.get('id'):
                            return value, response_headers
                        # Unsupported server requests are not silently executed.
                        if isinstance(value, dict) and 'method' in value and 'id' in value:
                            raise ToolUnavailable('server_requests_unsupported')
            raw = response.read(MAX_TOOL_BYTES+1)
            if len(raw) > MAX_TOOL_BYTES: raise ToolUnavailable('tool_response_too_large')
            value = json.loads(raw.decode('utf-8'))
            bounded_json(value)
            return value, response_headers
    except (URLError, HTTPError, OSError, ValueError, UnicodeError, RecursionError) as exc:
        raise ToolUnavailable('tool_unavailable') from exc


class MCPClient:
    def __init__(self, config, transport=request_json):
        self.config, self.transport = config, transport
        self.headers, self.counter = {}, 0

    def rpc(self, method, params):
        self.counter += 1
        request = {'jsonrpc': '2.0', 'id': self.counter, 'method': method, 'params': params}
        response, headers = self.transport(self.config, request, self.headers)
        if method == 'initialize':
            session_id = next((value for key, value in headers.items() if key.lower() == 'mcp-session-id'), None)
            if session_id:
                if not isinstance(session_id, str) or not re.fullmatch(r'[\x21-\x7e]{1,256}', session_id):
                    raise ToolUnavailable('invalid_mcp_session')
                self.headers['Mcp-Session-Id'] = session_id
        if not isinstance(response, dict) or response.get('jsonrpc') != '2.0' or response.get('id') != self.counter or 'error' in response or not isinstance(response.get('result'), dict):
            raise ToolUnavailable('invalid_mcp_response')
        return response['result']

    def discover(self):
        result = self.rpc('initialize', {'protocolVersion': PROTOCOL, 'capabilities': {},
                         'clientInfo': {'name': 'campusclaw', 'version': '1.0'}})
        if result.get('protocolVersion') != PROTOCOL or not isinstance(result.get('capabilities'), dict) or 'tools' not in result['capabilities']:
            raise ToolUnavailable('unsupported_mcp_server')
        self.headers['MCP-Protocol-Version'] = PROTOCOL
        self.transport(self.config, {'jsonrpc':'2.0','method':'notifications/initialized'}, self.headers, notification=True)
        tools, params, cursors = [], {}, set()
        for _ in range(5):
            result = self.rpc('tools/list', params)
            if not isinstance(result.get('tools'), list): raise ToolUnavailable('invalid_tool_list')
            tools.extend(result['tools'])
            if len(tools) > 32: raise ToolUnavailable('too_many_tools')
            cursor = result.get('nextCursor')
            if cursor is None: return tools
            if not isinstance(cursor, str) or cursor in cursors or len(cursor) > 1000: raise ToolUnavailable('invalid_cursor')
            cursors.add(cursor);params = {'cursor': cursor}
        raise ToolUnavailable('too_many_pages')

    def call(self, name, arguments):
        result = self.rpc('tools/call', {'name': name, 'arguments': arguments})
        if result.get('isError') or not isinstance(result.get('content'), list):
            raise ToolUnavailable('tool_execution_failed')
        bounded_json(result)
        return result

    def close(self):
        if 'Mcp-Session-Id' in self.headers:
            try: self.transport(self.config, None, self.headers, method='DELETE')
            except ToolUnavailable: pass
            self.headers = {}


class ToolRegistry:
    def __init__(self, configs, transport=request_json):
        self.entries, self.clients = {}, []
        self.transport = transport
        try:
            for config in configs:
                if config['type'] == 'mcp':
                    client = MCPClient(config, transport);self.clients.append(client)
                    items = client.discover()
                else:
                    client = None
                    items = [{'name': 'call', 'description': config['label'], 'inputSchema': config['input_schema']}]
                for item in items:
                    if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not 1 <= len(item['name']) <= 200:
                        raise ToolUnavailable('invalid_tool_name')
                    suffix = re.sub(r'[^a-zA-Z0-9_-]', '_', item['name'])[:25] + '_' + hashlib.sha256(item['name'].encode()).hexdigest()[:8]
                    name = config['id']+'__'+suffix
                    if name in self.entries: raise ToolUnavailable('duplicate_tool_name')
                    description = item.get('description', item['name'])
                    if not isinstance(description, str): raise ToolUnavailable('invalid_tool_description')
                    schema = validate_schema(item.get('inputSchema'))
                    definition = {'type':'function','function':{'name':name,'description':description[:1000],'parameters':schema}}
                    self.entries[name] = {'definition':definition, 'client':client, 'config':config, 'original':item['name']}
        except Exception:
            self.close()
            raise

    def definitions(self, names):
        if any(name not in self.entries for name in names): raise ToolUnavailable('unknown_tool')
        return [self.entries[name]['definition'] for name in names]

    def call(self, name, arguments):
        if name not in self.entries: raise ToolUnavailable('unknown_tool')
        item = self.entries[name]
        bounded_json(arguments, 16 * 1024)
        try: Draft202012Validator(item['definition']['function']['parameters']).validate(arguments)
        except (ValidationError, RecursionError) as exc: raise ToolUnavailable('invalid_tool_arguments') from exc
        if item['client']:
            return item['client'].call(item['original'], arguments)
        result, _ = self.transport(item['config'], arguments)
        if not isinstance(result, dict): raise ToolUnavailable('invalid_tool_result')
        bounded_json(result)
        return result

    def close(self):
        for client in self.clients: client.close()
