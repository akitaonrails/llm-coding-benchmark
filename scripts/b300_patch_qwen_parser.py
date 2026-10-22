"""Apply a narrowly scoped Qwen parser fix, preserving original serving source."""
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    path = Path(sys.prefix) / 'lib/python3.12/site-packages/vllm/parser/qwen3.py'
    source = path.read_text()
    marker = '# B300: preserve a trailing parameter only at a real function close.'
    if marker in source:
        print(json.dumps({'status': 'already_applied',
                          'after_sha256': hashlib.sha256(source.encode()).hexdigest()}))
        return
    old_converter = 'def _qwen3_arg_converter(raw_args: str, partial: bool) -> str:\n    params: dict[str, object] = {}'
    new_converter = ('def _qwen3_arg_converter(raw_args: str, partial: bool) -> str:\n'
                     '    ' + marker + '\n'
                     '    if raw_args.endswith(FUNC_END):\n'
                     '        raw_args = raw_args[:-len(FUNC_END)] + PARAM_END\n'
                     '    params: dict[str, object] = {}')
    old_transition = ('(ParserState.TOOL_ARGS, "FUNC_END"): Transition(\n'
                      '                ParserState.TOOL_BETWEEN,\n'
                      '                (EventType.TOOL_CALL_END,),\n'
                      '            ),')
    new_transition = old_transition.replace('(EventType.TOOL_CALL_END,),',
        '(EventType.ARG_VALUE_CHUNK, EventType.TOOL_CALL_END),')
    assert source.count(old_converter) == 1 and source.count(old_transition) == 1
    updated = source.replace(old_converter, new_converter).replace(old_transition, new_transition)
    compile(updated, str(path), 'exec')
    backup = Path('/root/logs') / f'qwen3-before-b300-{time.time_ns()}.py'
    backup.write_text(source)
    path.write_text(updated)
    print(json.dumps({'status': 'applied_requires_server_restart', 'backup': str(backup),
                     'before_sha256': hashlib.sha256(source.encode()).hexdigest(),
                     'after_sha256': hashlib.sha256(updated.encode()).hexdigest()}))


if __name__ == '__main__':
    main()
