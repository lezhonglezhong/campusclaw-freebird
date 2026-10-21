"""Immutable application instructions and safe, class-owned prompt templates."""
import re

APPLICATIONS = {
    'writing': {'id': 'writing', 'name': '写作润色', 'description': '改善表达，保留原意',
                'instruction': '你是写作助手。润色用户文本，保留原意，给出修改稿和简要修改说明。'},
    'study': {'id': 'study', 'name': '学习规划', 'description': '制定可执行的学习计划',
              'instruction': '你是学习规划助手。根据目标制定分阶段计划，列出行动、检查点和复习安排。'},
    'exercises': {'id': 'exercises', 'name': '练习生成', 'description': '生成练习、答案与解析',
                  'instruction': '你是练习设计助手。根据用户主题生成三道练习，并分别提供答案和解析。'},
}
DEFAULT_TEMPLATE = '请针对以下内容提供帮助：\n{{input}}\n目标读者：{{audience}}'
VARIABLE = re.compile(r'\{\{(.*?)\}\}', re.DOTALL)


def text_field(value, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError('invalid_text')
    return value.strip()


def validate_template(content):
    content = text_field(content, 8000)
    if any(name not in {'input', 'audience'} for name in VARIABLE.findall(content)):
        raise ValueError('invalid_variable')
    if '{{' in VARIABLE.sub('', content) or '}}' in VARIABLE.sub('', content):
        raise ValueError('invalid_variable')
    return content


def render_template(content, user_input, audience):
    validate_template(content)
    # Single-pass substitution: user strings are never reinterpreted as templates.
    values = {'input': user_input, 'audience': audience}
    return VARIABLE.sub(lambda match: values[match.group(1)], content)
