"""CPU-only diagnostic; never executes generated tool calls or changes vLLM."""
import json
import sys
from unittest.mock import MagicMock

from vllm.entrypoints.openai.chat_completion.protocol import ChatCompletionRequest
from vllm.parser.engine.parser_engine import ParserEngine
from vllm.parser.qwen3 import qwen3_config


def parser_and_request(typed=False):
    tokenizer = MagicMock()
    vocab = {'<tool_call>': 1000, '</tool_call>': 1001}
    tokenizer.get_vocab.return_value = vocab
    tokenizer.all_special_tokens = list(vocab)
    tokenizer.all_special_ids = list(vocab.values())
    tokenizer.encode.return_value = [1, 2, 3]
    request = MagicMock(spec=ChatCompletionRequest)
    request.tools = []
    request.tool_choice = 'auto'
    request.include_reasoning = True
    if typed:
        request = ChatCompletionRequest(model='fixture', messages=[], tools=[{
            'type': 'function', 'function': {'name': 'read', 'parameters': {
                'type': 'object', 'properties': {
                    'filePath': {'type': 'string'}, 'offset': {'type': 'integer'}}}}}])
    return ParserEngine(tokenizer, tools=request.tools,
                        parser_engine_config=qwen3_config(thinking=False)), request


def check(text, width=1, typed=False):
    parser, request = parser_and_request(typed)
    result = parser.extract_tool_calls(text, request)
    whole = [json.loads(c.function.arguments) for c in result.tool_calls]
    parser, request = parser_and_request(typed)
    previous = ''
    streamed = ''
    for start in range(0, len(text), width):
        char = text[start:start + width]
        current = previous + char
        delta = parser.extract_tool_calls_streaming(
            previous_text=previous, current_text=current, delta_text=char,
            previous_token_ids=(), current_token_ids=(), delta_token_ids=(),
            request=request)
        if delta and delta.tool_calls:
            for call in delta.tool_calls:
                if call.function and call.function.arguments:
                    streamed += call.function.arguments
        previous = current
    return {'whole': whole, 'streamed': streamed}


if __name__ == '__main__':
    if '--proposed-fix' in sys.argv:
        import vllm.parser.qwen3 as qwen
        from vllm.parser.engine.events import EventType
        from vllm.parser.engine.parser_engine_config import ParserState, Transition
        original = qwen._qwen3_arg_converter

        def closed_tail(raw_args, partial):
            if raw_args.endswith(qwen.FUNC_END):
                raw_args = raw_args[:-len(qwen.FUNC_END)] + qwen.PARAM_END
            return original(raw_args, partial)

        qwen._qwen3_arg_converter = closed_tail
        qwen.qwen3_config.cache_clear()
        config = qwen.qwen3_config(thinking=False)
        config.transitions[(ParserState.TOOL_ARGS, 'FUNC_END')] = Transition(
            ParserState.TOOL_BETWEEN,
            (EventType.ARG_VALUE_CHUNK, EventType.TOOL_CALL_END))
    prefix = '<tool_call><function=read><parameter=filePath>/tmp/fixture.txt</parameter><parameter=offset>1'
    cases = {
        'well_formed': prefix + '</parameter></function></tool_call>',
        'function_closed_last_parameter_unclosed': prefix + '</function></tool_call>',
        'actually_truncated': prefix,
    }
    results = {}
    for typed in (False, True):
        for width in (1, 3, 8, 256):
            for name, text in cases.items():
                result = check(text, width, typed)
                results[f'{name}/typed={typed}/chunk={width}'] = result
                if '--assert-fixed' in sys.argv or '--proposed-fix' in sys.argv:
                    if name == 'actually_truncated':
                        assert 'offset' not in result['whole'][0]
                        try:
                            json.loads(result['streamed'])
                        except json.JSONDecodeError:
                            pass
                        else:
                            raise AssertionError('Truncated arguments became complete')
                    else:
                        expected = {'filePath': '/tmp/fixture.txt', 'offset': 1 if typed else '1'}
                        assert result['whole'] == [expected], result
                        assert json.loads(result['streamed']) == expected, result
    print(json.dumps(results, indent=2))
