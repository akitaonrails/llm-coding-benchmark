#!/usr/bin/env python3
"""Supplemental observable outputs; task-state traces are not private reasoning."""
import argparse
from collections import Counter,defaultdict
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import re
import statistics
import sys
import time
import experiment as e

SYSTEM='Follow the requested response format exactly. Do not use external tools.'


def probes():
    out=[]
    for family in ['numeric','symbolic']:
        for seed in range(4):
            for length in [4,12]:
                rng=random.Random(49001+seed*100+length)
                if family=='numeric':
                    state=rng.randrange(17);initial=state;ops=[];states=[]
                    for _ in range(length):
                        mul,add=rng.randint(2,9),rng.randint(1,13)
                        ops.append(f'x = (x * {mul} + {add}) modulo 31')
                        state=(state*mul+add)%31;states.append(str(state))
                    question=f'Start with x={initial}. Apply these updates in order: '+ '; '.join(ops)+'.'
                else:
                    state=''.join(rng.choice('abcd') for _ in range(13));initial=state;ops=[];states=[]
                    for _ in range(length):
                        op=rng.choice(['reverse','rotate','swap'])
                        if op=='reverse':ops.append('reverse the entire string');state=state[::-1]
                        elif op=='rotate':ops.append('rotate the string left by 3 characters');state=state[3:]+state[:3]
                        else:ops.append('swap every a with b and every b with a simultaneously');state=state.translate(str.maketrans('ab','ba'))
                        states.append(state)
                    question=f'Start with the string {initial}. Apply these operations in order: '+ '; '.join(ops)+'.'
                for mode in ['answer','check','trace']:
                    suffix={
                        'answer':' Return only the final value, no other text.',
                        'check':' Return a JSON object with "answer" (final value as a string) and "check" (one brief sentence describing a way to verify it). No other text.',
                        'trace':' Return a JSON object with "answer" (final value as a string) and "states" (an array of strings giving the value after each listed operation, excluding the initial value). These states are the requested task output. No other text.'}[mode]
                    out.append(dict(id=f'{family}-{seed}-{length}-{mode}',family=family,block=f'{family}-{seed}-{length}',mode=mode,steps=length,prompt=question+suffix,expected=states[-1],states=states))
    return out


def sealed_manifest(name,after):
    path=e.kit.run_path(name);path.mkdir(parents=True,exist_ok=False)
    profiles=[p for p in e.configs() if p['label'] in ['gpt4o-a','gpt4o-verify','genesys']]
    profiles.append(dict(label='gptoss',base_url='https://openrouter.ai/api/v1',model='openai/gpt-oss-120b',key_env='OPENROUTER_API_KEY',wrapper='plain'))
    bank=probes();plan=e.schedule(bank,[p['label'] for p in profiles],3,9051)
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),e.ROOT/'experiment.py',e.ROOT/'panel.py',e.ROOT.parent/'kit.py']}
    manifest=e.seal(dict(name=name,created_at=e.kit.now(),after_tokenizer=after,profiles=profiles,probes=bank,schedule=plan,source_hashes=files,
        system=SYSTEM,max_tokens=1536,timeout=90,minimum_interval_seconds=1,temperature=None,interpretation='Exploratory output/process indicators, not the confirmatory attribution threshold. Three replicates per condition; no identity probability.'))
    e.atomic(path/'manifest.json',manifest)
    for sub in ['records','started','calls','source']:(path/sub).mkdir()
    for source in [Path(__file__),e.ROOT/'experiment.py',e.ROOT/'panel.py',e.ROOT.parent/'kit.py']:(path/'source'/source.name).write_bytes(source.read_bytes())
    print(f'Planned {len(plan)} output observations, at most {len(plan)+len(plan)//4} physical calls.',flush=True)
    return manifest


def parse(row,p):
    result=dict(usable=False,answer=None,correct=None,first_wrong_step=None,trace=None,check=None)
    if row['status']!='ok':return result
    text=row.get('text','').strip()
    if p['mode']=='answer':answer=text
    else:
        try:
            d=json.loads(text)
            if not isinstance(d,dict) or not isinstance(d.get('answer'),str):return result
            answer=d['answer']
            if p['mode']=='trace':
                states=d.get('states')
                if not isinstance(states,list) or not all(isinstance(x,str) for x in states):return result
                result['trace']=states
                result['first_wrong_step']=next((i+1 for i,(x,y) in enumerate(itertools.zip_longest(states,p['states'])) if x!=y),None)
            else:
                if not isinstance(d.get('check'),str):return result
                result['check']=d['check']
        except (ValueError,TypeError):return result
    result.update(usable=True,answer=answer,correct=answer==p['expected'])
    return result


def check_similarity(left,right):
    def features(text):
        words=re.findall(r"[^\W\d_]+",text.lower())
        return set(zip(words,words[1:]))
    a,b=features(left),features(right)
    return len(a&b)/len(a|b) if a|b else None


def report(path,m):
    rows=[e.read_sealed(p) for p in sorted((path/'records').glob('*.json'))]
    probes_by_id={p['id']:p for p in m['probes']};groups=defaultdict(list);details=[]
    for row in rows:
        p=probes_by_id[row['request']['probe']];v=parse(row,p)
        usage=row.get('usage') if isinstance(row.get('usage'),dict) else {};tokens=usage.get('completion_tokens_details');tokens=tokens if isinstance(tokens,dict) else {};reasoning=tokens.get('reasoning_tokens')
        d=dict(profile=row['request']['profile'],probe=p['id'],mode=p['mode'],status=row['status'],elapsed_seconds=sum(c.get('elapsed_seconds',0) for c in row['calls']),
            reported_reasoning_tokens=reasoning,returned_tokens_over_request=any(c.get('reported_completion_tokens_exceed_request') for c in row['calls']),
            response_model=row.get('response_model'),system_fingerprint=row.get('system_fingerprint'),**v)
        groups[(d['profile'],p['mode'])].append(d);details.append(d)
    summaries={}
    for (profile,mode),ds in groups.items():
        usable=[d for d in ds if d['usable']];rt=[d['reported_reasoning_tokens'] for d in ds if type(d['reported_reasoning_tokens']) is int]
        summaries[f'{profile}:{mode}']=dict(recorded=len(ds),usable=len(usable),correct=sum(d['correct'] for d in usable),
            status_counts=dict(Counter(d['status'] for d in ds)),median_elapsed=statistics.median(d['elapsed_seconds'] for d in ds),
            reasoning_tokens_reported=len(rt),median_reported_reasoning_tokens=statistics.median(rt) if rt else None,
            incorrect_task_traces=sum(d['trace'] is not None and d['first_wrong_step'] is not None for d in usable),
            request_limit_exceeded=sum(d['returned_tokens_over_request'] for d in ds))
    comparisons=[]
    for left,right in itertools.combinations([p['label'] for p in m['profiles']],2):
        pair=[]
        for p in m['probes']:
            x=[d for d in details if d['profile']==left and d['probe']==p['id'] and d['usable']]
            y=[d for d in details if d['profile']==right and d['probe']==p['id'] and d['usable']]
            if not x or not y:continue
            n=len(x)*len(y)
            pair.append(dict(probe=p['id'],left_samples=len(x),right_samples=len(y),
                same_answer=sum(a['answer']==b['answer'] for a in x for b in y)/n,
                same_wrong_answer=sum(a['answer']==b['answer'] and not a['correct'] for a in x for b in y)/n,
                same_wrong_trace=sum(a['trace']==b['trace'] and a['first_wrong_step'] is not None for a in x for b in y)/n if p['mode']=='trace' else None,
                check_bigram_jaccard_mean=statistics.mean(v for a in x for b in y if (v:=check_similarity(a['check'],b['check'])) is not None) if p['mode']=='check' and any(check_similarity(a['check'],b['check']) is not None for a in x for b in y) else None))
        comparisons.append(dict(left=left,right=right,details=pair))
    data=e.seal(dict(manifest_sha256=m['sha256'],summaries=summaries,comparisons=comparisons,observations=details,
        limitation='Visible checks are generated explanations; explicit task-state sequences are verifiable outputs, not internal reasoning. Token counts are provider claims. Latency includes hosting/load and is not an architecture measurement. Concurrent reference collection may affect timing.'))
    e.atomic(path/'analysis.json',data)
    lines=['# Observable outputs and process indicators','',data['limitation'],'','Exploratory supplement; this does not alter the frozen main calibration threshold.','',
        '| Profile:condition | Usable/recorded | Correct answers | Incorrect traces | Median seconds | Median reported reasoning tokens |','|---|---:|---:|---:|---:|---:|']
    for label,s in summaries.items():lines.append(f"| {label} | {s['usable']}/{s['recorded']} | {s['correct']} | {s['incorrect_task_traces']} | {s['median_elapsed']:.2f} | {s['median_reported_reasoning_tokens']} |")
    lines+=['','Per-task matching wrong answers, identical wrong state sequences, visible verification sentences and metadata appear in analysis.json. High agreement on correct answers is not distinctive evidence.','']
    (path/'report.md').write_text('\n'.join(lines))


def run(name):
    path=e.kit.run_path(name);m=e.read_sealed(path/'manifest.json')
    for source in [Path(__file__),e.ROOT/'experiment.py',e.ROOT/'panel.py',e.ROOT.parent/'kit.py']:
        if hashlib.sha256(source.read_bytes()).hexdigest()!=m['source_hashes'][source.name]:raise ValueError('Frozen supplement source changed')
    with e.kit.locked(path):
        if m['after_tokenizer']:
            parent=e.kit.run_path(m['after_tokenizer'])
            while not (parent/'tokenizer/complete.json').exists():
                e.atomic(path/'status.json',dict(status='waiting_for_tokenizer',updated_at=e.kit.now()))
                if (parent/'status.json').exists() and json.loads((parent/'status.json').read_text()).get('status')=='stopped':raise RuntimeError('Parent experiment stopped')
                time.sleep(30)
        bank={p['id']:p for p in m['probes']};profiles={p['label']:p for p in m['profiles']}
        secrets=[os.environ[p['key_env']] for p in m['profiles']]
        failures=Counter()
        for idx,task in enumerate(m['schedule']):
            dest=path/'records'/f"{task['id']}.json";started=path/'started'/f"{task['id']}.json"
            if dest.exists():e.read_sealed(dest);continue
            if started.exists():
                e.atomic(dest,e.seal(dict(request=task,status='interrupted_unknown',calls=[])));continue
            e.atomic(started,e.seal(dict(request=task,started_at=e.kit.now())))
            profile=profiles[task['profile']];p=bank[task['probe']]
            messages=[dict(role='system',content=m['system']),dict(role='user',content=p['prompt'])];calls=[]
            for turn in range(2 if profile['wrapper']=='verify' else 1):
                if failures[profile['label']]>=3:
                    calls.append(dict(status='circuit_open'));break
                e.atomic(path/'calls'/f"{task['id']}-{turn}.started.json",e.seal(dict(request=task,turn=turn,started_at=e.kit.now())))
                r=e.http_call(profile,messages,m['max_tokens'],m['timeout'],secrets)
                e.atomic(path/'calls'/f"{task['id']}-{turn}.json",e.seal(r));calls.append(r)
                failures[profile['label']]=failures[profile['label']]+1 if r['status'] not in ('ok','truncated','empty','nonstandard_finish') else 0
                if r.get('http_status')==429:time.sleep(60)
                time.sleep(m['minimum_interval_seconds'])
                if r['status']!='ok':break
                messages += [dict(role='assistant',content=r['text']),dict(role='user',content='Verify the candidate against the original task and correct mistakes. Return the answer using exactly the originally requested format.')]
            e.atomic(dest,e.seal(dict(request=task,**calls[-1],calls=calls)))
            e.atomic(path/'status.json',dict(status='running',completed=idx+1,planned=len(m['schedule']),updated_at=e.kit.now()))
            if (idx+1)%8==0:
                print(f'Outputs {idx+1}/{len(m["schedule"])}',flush=True)
                report(path,m)
        report(path,m);e.atomic(path/'status.json',dict(status='completed',completed=len(m['schedule']),updated_at=e.kit.now()))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','run','report']);p.add_argument('name');p.add_argument('--after-tokenizer')
    args=p.parse_args()
    if args.command=='plan':sealed_manifest(args.name,args.after_tokenizer)
    elif args.command=='report':report(e.kit.run_path(args.name),e.read_sealed(e.kit.run_path(args.name)/'manifest.json'))
    else:
        try:run(args.name)
        except BaseException as exc:
            e.atomic(e.kit.run_path(args.name)/'status.json',dict(status='stopped',error_type=type(exc).__name__,updated_at=e.kit.now()));raise

if __name__=='__main__':main()
