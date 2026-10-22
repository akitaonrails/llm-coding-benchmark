#!/usr/bin/env python3
"""Check authenticated chat and a streamed tool/result round trip before a sprint."""
import argparse
import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def request(base, key, body):
    req = urllib.request.Request(base + '/chat/completions',
        data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + key,
        'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as response:
        if not body.get('stream'):
            return json.load(response)
        content, calls, events = '', {}, []
        for raw in response:
            line = raw.decode().strip()
            if not line.startswith('data: ') or line == 'data: [DONE]':
                continue
            event = json.loads(line[6:]); events.append(event)
            for choice in event.get('choices', []):
                delta = choice.get('delta', {})
                content += delta.get('content') or ''
                for call in delta.get('tool_calls') or []:
                    obj = calls.setdefault(call['index'], {'id': '', 'type': 'function',
                        'function': {'name': '', 'arguments': ''}})
                    if call.get('id'): obj['id'] = call['id']
                    fn = call.get('function', {})
                    obj['function']['name'] += fn.get('name') or ''
                    obj['function']['arguments'] += fn.get('arguments') or ''
        message = {'role': 'assistant', 'content': content or None}
        if calls: message['tool_calls'] = [calls[i] for i in sorted(calls)]
        return {'message': message, 'events': events}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('slug'); a = ap.parse_args()
    config = json.loads((ROOT/'config/opencode.benchmark.json').read_text())
    p = config['provider']['runpod-vllm']['options']
    q = next(q for q in json.loads((ROOT/'config/b300_campaign.json').read_text())['queue'] if q['slug'] == a.slug)
    output = ROOT/'results-v4/_b300_campaign/migration-20261017'/f'preflight-{a.slug}-{time.time_ns()}.json'
    evidence = {'slug': a.slug, 'started_at': time.time(), 'checks': {}, 'responses': {}}
    try:
        body = {'model': q['served_name'], 'max_tokens': 2048,
                'messages': [{'role': 'user', 'content': 'Reply with just the number: 2+2.'}]}
        chat = request(p['baseURL'], p['apiKey'], body)
        evidence['responses']['chat'] = chat
        evidence['checks']['chat'] = bool(re.search(r'\b4\b', chat['choices'][0]['message'].get('content') or ''))
        tools = [{'type': 'function', 'function': {'name': 'lookup_probe_code',
            'description': 'Look up the diagnostic code for the specified record.',
            'parameters': {'type': 'object', 'properties': {'record': {'type': 'string'}}, 'required': ['record']}}}]
        messages = [{'role': 'user', 'content': 'Use lookup_probe_code for record b300-check. After the tool returns, reply with its code exactly.'}]
        body = {'model': q['served_name'], 'messages': messages, 'tools': tools,
                'tool_choice': 'auto', 'max_tokens': 2048, 'stream': True}
        result = request(p['baseURL'], p['apiKey'], body)
        evidence['responses']['tool_request'] = result
        msg = result['message']; calls = msg.get('tool_calls') or []
        valid = len(calls) == 1 and calls[0]['function']['name'] == 'lookup_probe_code' and json.loads(calls[0]['function']['arguments']) == {'record': 'b300-check'}
        evidence['checks']['streamed_tool_call'] = valid
        if valid:
            code = 'B300_CHECK_72941'
            messages.extend([msg, {'role': 'tool', 'tool_call_id': calls[0]['id'], 'content': json.dumps({'code': code})}])
            follow = request(p['baseURL'], p['apiKey'], body)
            evidence['responses']['tool_result'] = follow
            evidence['checks']['tool_result_round_trip'] = code in (follow['message'].get('content') or '')
        else:
            evidence['checks']['tool_result_round_trip'] = False
    except urllib.error.HTTPError as e:
        evidence['error'] = {'type': 'HTTPError', 'status': e.code}
    except Exception as e:
        evidence['error'] = {'type': type(e).__name__, 'message': str(e)[:300]}
    evidence['passed'] = len(evidence['checks']) == 3 and all(evidence['checks'].values()) and 'error' not in evidence
    evidence['finished_at'] = time.time()
    output.write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps({**{k: evidence[k] for k in ('slug','checks','passed')}, 'evidence': str(output)}))
    return 0 if evidence['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
