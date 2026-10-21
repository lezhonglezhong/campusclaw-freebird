"""Strict declarative skill manifests and bounded sequential execution."""
import json
from campusclaw.platform_catalog import text_field

MAX_SKILL_BYTES = 16 * 1024
BUILTIN_SKILLS = {
    'draft-review': {'version': 1, 'name': '起草与审校', 'description': '先起草，再检查并完善输出',
        'instructions': '保持事实准确，按用户要求输出。审校阶段必须修正初稿问题。',
        'steps': [{'name': '起草', 'instruction': '根据当前任务生成完整初稿。'},
                  {'name': '审校', 'instruction': '检查上一阶段输出，修正遗漏和表达问题，返回最终完整版本。'}]},
    'learning-coach': {'version': 1, 'name': '学习教练', 'description': '先分析学习目标，再给出行动方案',
        'instructions': '面向学生给出清晰、可执行的学习建议。',
        'steps': [{'name': '分析目标', 'instruction': '识别任务的知识点、难点和学习目标。'},
                  {'name': '行动方案', 'instruction': '基于上一阶段分析，完成用户请求并给出检查学习效果的方法。'}]},
}


def validate_skill(value):
    if not isinstance(value, dict) or set(value) != {'version', 'name', 'description', 'instructions', 'steps'}:
        raise ValueError('invalid_skill')
    if type(value['version']) is not int or value['version'] != 1:
        raise ValueError('invalid_version')
    for key, limit in [('name', 120), ('description', 500), ('instructions', 4000)]:
        text_field(value[key], limit)
    steps = value['steps']
    if not isinstance(steps, list) or not 1 <= len(steps) <= 3:
        raise ValueError('invalid_steps')
    for step in steps:
        if not isinstance(step, dict) or set(step) != {'name', 'instruction'}:
            raise ValueError('invalid_step')
        text_field(step['name'], 120)
        text_field(step['instruction'], 2000)
    if len(json.dumps(value, ensure_ascii=False).encode()) > MAX_SKILL_BYTES:
        raise ValueError('skill_too_large')
    return value


def parse_skill(raw):
    if len(raw) > MAX_SKILL_BYTES:
        raise ValueError('skill_too_large')
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('duplicate_key')
            result[key] = value
        return result
    try:
        return validate_skill(json.loads(raw.decode('utf-8'), object_pairs_hook=unique_pairs))
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('invalid_skill') from exc


def execute_skill(manifest, generate, events):
    """The callback executes a model stage; failures stop the workflow immediately."""
    validate_skill(manifest)
    full_manifest = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    previous = ''
    for index, step in enumerate(manifest['steps'], 1):
        event = {'step': index, 'name': step['name'], 'status': 'running'}
        events.append(event)
        try:
            previous = generate(step['instruction'], previous, full_manifest)
        except Exception:
            event['status'] = 'failed'
            raise
        event.update(status='completed', output=previous)
    return previous
