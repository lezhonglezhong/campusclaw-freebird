"""Observable bounded Chat Completions exchanges including function-call continuation."""
import copy
import json
from campusclaw.ai_providers import ProviderUnavailable, _check_payload_size, _post_json
from campusclaw.platform_tools import ToolUnavailable, bounded_json


class PlatformChat:
    def __init__(self, settings, transport=_post_json):
        self.settings, self.transport = settings, transport

    def exchange(self, messages, definitions, exchanges):
        if not self.settings.chat_base_url or not self.settings.chat_api_key:
            raise ProviderUnavailable('chat_unavailable')
        payload = {'model': self.settings.chat_model, 'messages': copy.deepcopy(messages)}
        if definitions: payload.update(tools=definitions, tool_choice='auto')
        _check_payload_size(payload)
        event = {'request': copy.deepcopy(payload), 'status':'pending'}
        exchanges.append(event)
        response = self.transport(self.settings.chat_base_url+'/chat/completions', payload,
                                  self.settings.chat_api_key, self.settings.timeout_seconds)
        bounded_json(response, 128 * 1024)
        event.update(response=copy.deepcopy(response), status='received')
        choices = response.get('choices') if isinstance(response, dict) else None
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ProviderUnavailable('invalid_chat_response')
        message = choices[0].get('message')
        if not isinstance(message, dict) or message.get('role', 'assistant') != 'assistant':
            raise ProviderUnavailable('invalid_chat_response')
        return message


def generate_with_tools(chat, messages, registry, selected, trace, budget):
    definitions = registry.definitions(selected) if registry else []
    for _ in range(3):
        message = chat.exchange(messages, definitions, trace['exchanges'])
        calls = message.get('tool_calls')
        if not calls:
            content = message.get('content')
            if not isinstance(content, str) or not content.strip() or len(content) > 8000:
                raise ProviderUnavailable('invalid_chat_response')
            return content.strip()
        if not isinstance(calls, list) or not calls or len(calls)+budget['calls'] > 4:
            raise ToolUnavailable('tool_limit')
        parsed, ids = [], set()
        # Validate every call before invoking any member of a parallel batch.
        for call in calls:
            if not isinstance(call, dict) or call.get('type') != 'function': raise ToolUnavailable('invalid_tool_call')
            call_id, function = call.get('id'), call.get('function')
            if not isinstance(call_id,str) or not 1 <= len(call_id) <= 200 or call_id in ids or call_id in budget['ids'] or not isinstance(function,dict):
                raise ToolUnavailable('invalid_tool_call')
            ids.add(call_id)
            name, raw = function.get('name'), function.get('arguments')
            if not isinstance(name, str) or name not in selected or not isinstance(raw,str) or len(raw)>16000:
                raise ToolUnavailable('unknown_tool')
            try: arguments = json.loads(raw)
            except (ValueError, RecursionError) as exc: raise ToolUnavailable('invalid_tool_arguments') from exc
            # Schema validation before the batch has any effects.
            from jsonschema import Draft202012Validator, ValidationError
            try:
                bounded_json(arguments, 16*1024)
                Draft202012Validator(registry.entries[name]['definition']['function']['parameters']).validate(arguments)
            except (ValidationError, RecursionError) as exc: raise ToolUnavailable('invalid_tool_arguments') from exc
            parsed.append((call_id,name,arguments))
        messages.append({'role':'assistant','content':message.get('content'), 'tool_calls':calls})
        budget['ids'].update(ids)
        for call_id,name,arguments in parsed:
            budget['calls'] += 1
            event = {'id':call_id,'name':name,'arguments':arguments,'status':'running'}
            trace['tools'].append(event)
            try: result = registry.call(name, arguments)
            except ProviderUnavailable:
                event['status'] = 'failed'
                raise
            event.update(status='completed',result=result)
            messages.append({'role':'tool','tool_call_id':call_id,'content':json.dumps(result,ensure_ascii=False)})
    raise ToolUnavailable('chat_round_limit')
