#!/usr/bin/env python3
"""Frozen, resumable forensic experiment; never executes generated model code."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random
import sys
import threading
import time
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
import kit
from panel import behavioral,tokens,FAMILIES

BASE_SYSTEM='Follow the user instruction exactly. Return only the requested final answer, without explanation.'
ALT_SYSTEM='You are a careful assistant. Check the task and formatting before answering. Keep your final response to the requested answer only.'
FILES=['experiment.py','panel.py','analysis.py','PROTOCOL.md']


def atomic(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:
        f.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
    tmp.replace(path)


def seal(value):
    return {**value,'sha256':kit.digest(value)}


def read_sealed(path):
    d=json.loads(path.read_text());h=d.pop('sha256')
    if kit.digest(d)!=h:raise ValueError(f'Integrity failure: {path.name}')
    return {**d,'sha256':h}


def hashes():
    return {**{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES},'../kit.py':hashlib.sha256((ROOT.parent/'kit.py').read_bytes()).hexdigest()}


def configs():
    def ref(label,model,wrapper='plain'):
        return dict(label=label,base_url='https://openrouter.ai/api/v1',model=model,key_env='OPENROUTER_API_KEY',wrapper=wrapper)
    gpt='openai/gpt-4o-2024-08-06'
    return [ref('gpt4o-a',gpt),ref('gpt4o-b',gpt),ref('gpt4o-system',gpt,'system'),
        ref('gpt4o-verify',gpt,'verify'),ref('gpt4o-snapshot','openai/gpt-4o-2024-11-20'),
        ref('qwen','qwen/qwen3-max'),ref('qwen-verify','qwen/qwen3-max','verify'),
        ref('llama','meta-llama/llama-3.3-70b-instruct'),
        dict(label='genesys',base_url='https://api.lua.vision/v1',model='genesys-pi-house',key_env='LUA_API_KEY',wrapper='plain')]


def schedule(probes,labels,repeats,seed):
    r=random.Random(seed);out=[]
    for rep in range(repeats):
        for p in r.sample(probes,len(probes)):
            for label in r.sample(labels,len(labels)):
                out.append(dict(id=f'{len(out):06}',probe=p['id'],profile=label,replicate=rep))
    return out


def plan(name):
    import tiktoken
    path=kit.run_path(name);path.mkdir(parents=True,exist_ok=False)
    discovery,holdout,choices=behavioral(); strings=tokens()
    encodings={}
    for encoding in ['o200k_base','cl100k_base']:
        enc=tiktoken.get_encoding(encoding)
        # Hash actual merge table; inputs encoded without special-token interpretation.
        table=sorted((k.hex(),v) for k,v in enc._mergeable_ranks.items())
        encodings[encoding]=dict(table_sha256=kit.digest(table),counts={p['id']:len(enc.encode(p['prompt'],disallowed_special=())) for p in strings})
    m=seal(dict(name=name,created_at=kit.now(),schema=2,code=hashes(),python=sys.version,
        tiktoken=importlib.metadata.version('tiktoken'),encodings=encodings,profiles=configs(),
        sampling='provider defaults; temperature omitted',max_tokens=512,timeout_seconds=90,
        discovery=discovery,holdout_bank=holdout,perturbations=choices,tokens=strings,
        settings=dict(workers=8,endpoint_concurrency=2,min_interval_seconds=.5,rate_cooldown_seconds=60,replicates=6),
        phase_order=['tokenizer','discovery','calibration','target','temporal']))
    atomic(path/'manifest.json',m)
    (path/'source').mkdir()
    for f in FILES:(path/'source'/f).write_bytes((ROOT/f).read_bytes())
    (path/'source'/'kit.py').write_bytes((ROOT.parent/'kit.py').read_bytes())
    print(f'Frozen {name}: 1024 tokenizer strings, 48 discovery probes, up to 64 holdout probes; at most 6824 physical calls.',flush=True)
    return m


class Limiter:
    def __init__(self,settings):
        self.settings=settings;self.sem=threading.Semaphore(settings['endpoint_concurrency'])
        self.lock=threading.Lock();self.next_start=0.;self.failures=0;self.open=False
    def reserve(self):
        with self.lock:
            if self.open:return False
            delay=max(0,self.next_start-time.monotonic())
            self.next_start=max(self.next_start,time.monotonic())+self.settings['min_interval_seconds']
        if delay:time.sleep(delay)
        with self.lock:return not self.open
    def finish(self,row):
        failed=row['status'] not in ('ok','truncated','empty','nonstandard_finish')
        with self.lock:
            if row.get('http_status')==429:
                self.next_start=max(self.next_start,time.monotonic()+self.settings['rate_cooldown_seconds'])
            self.failures=self.failures+1 if failed else 0
            if self.failures>=3:self.open=True


def http_call(profile,messages,max_tokens,timeout,secrets):
    body=dict(model=profile['model'],messages=messages,max_tokens=max_tokens,stream=False)
    req=urllib.request.Request(profile['base_url']+'/chat/completions',data=kit.canonical(body).encode(),
        headers={'Authorization':'Bearer '+os.environ[profile['key_env']],'Content-Type':'application/json'})
    started=time.monotonic();out=dict(started_at=kit.now(),request_sha256=kit.digest(body))
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),kit.NoRedirect())
    try:
        with opener.open(req,timeout=timeout) as r:
            out['http_status']=r.status;raw=r.read(2_000_001)
            if len(raw)>2_000_000:out['status']='oversize_response'
            else:
                try:
                    d=json.loads(raw)
                    if isinstance(d,dict) and d.get('error'):
                        out.update(status='provider_error',error=d['error'])
                    else:
                        c=d['choices'][0];text=c['message'].get('content');finish=c.get('finish_reason')
                        if text is not None and not isinstance(text,str):raise TypeError()
                        out.update(status='truncated' if finish=='length' else 'empty' if not text else 'ok' if finish=='stop' else 'nonstandard_finish',
                            text=text,finish_reason=finish,usage=d.get('usage'),response_model=d.get('model'),provider=d.get('provider'),system_fingerprint=d.get('system_fingerprint'))
                except (ValueError,TypeError,KeyError,IndexError,AttributeError):out['status']='invalid_response'
    except urllib.error.HTTPError as e:
        out.update(status='http_error',http_status=e.code)
        try:
            d=json.loads(e.read(16000));out['error']=d.get('error') if isinstance(d,dict) else None
        except (ValueError,OSError):pass
        finally:e.close()
    except (urllib.error.URLError,TimeoutError,OSError) as e:out.update(status='transport_error',error_type=type(e).__name__)
    usage=out.get('usage')
    reported=usage.get('completion_tokens') if isinstance(usage,dict) else None
    out.update(requested_max_tokens=max_tokens,reported_completion_tokens_exceed_request=isinstance(reported,int) and reported>max_tokens,finished_at=kit.now(),elapsed_seconds=round(time.monotonic()-started,6))
    return kit.redact(out,secrets)


def observation(task,probe,profile,m,phase,limiter,secrets):
    started=phase/'started'/f"{task['id']}.json";output=phase/'records'/f"{task['id']}.json"
    if output.exists():return read_sealed(output)
    if started.exists():
        row=seal(dict(request=task,status='interrupted_unknown',finished_at=kit.now(),calls=[]));atomic(output,row);return row
    atomic(started,seal(dict(request=task,started_at=kit.now())))
    messages=[dict(role='system',content=ALT_SYSTEM if profile['wrapper']=='system' else BASE_SYSTEM),dict(role='user',content=probe['prompt'])]
    calls=[]
    with limiter.sem:
        for turn in range(2 if profile['wrapper']=='verify' and probe['kind']!='tokens' else 1):
            if not limiter.reserve():
                calls.append(dict(status='circuit_open',finished_at=kit.now()));break
            pending=phase/'calls'/f"{task['id']}-{turn}.started.json"
            atomic(pending,seal(dict(request=task,turn=turn,started_at=kit.now())))
            r=http_call(profile,messages,1 if probe['kind']=='tokens' else m['max_tokens'],m['timeout_seconds'],secrets)
            atomic(phase/'calls'/f"{task['id']}-{turn}.json",seal(r));calls.append(r);limiter.finish(r)
            if r['status']!='ok':break
            if turn==0 and profile['wrapper']=='verify':
                messages += [dict(role='assistant',content=r['text']),dict(role='user',content='Independently check the preceding candidate against the original task. Correct any mistake. Return only the final answer in the originally requested format.')]
    last=calls[-1]
    row=seal(dict(request=task,**last,calls=calls,observation_finished_at=kit.now()))
    atomic(output,row)
    return row


def phase_rows(path):
    return [read_sealed(p) for p in sorted((path/'records').glob('*.json'))]


def run_phase(path,m,name,probes,labels,repeats):
    phase=path/name;phase.mkdir(exist_ok=True)
    for sub in ['records','started','calls']:(phase/sub).mkdir(exist_ok=True)
    spec=seal(dict(name=name,parent=m['sha256'],probes=probes,labels=labels,repeats=repeats,
        schedule=schedule(probes,labels,repeats,seed=5401)))
    if (phase/'plan.json').exists():
        if read_sealed(phase/'plan.json')!=spec:raise ValueError('Phase changed after freeze')
    else:atomic(phase/'plan.json',spec)
    if (phase/'complete.json').exists():
        completion=read_sealed(phase/'complete.json');rows=phase_rows(phase)
        if completion['records_sha256']!=kit.digest(rows):raise ValueError('Completed phase changed')
        return rows
    profiles={p['label']:p for p in m['profiles']};bank={p['id']:p for p in probes}
    selected=[profiles[k] for k in labels]
    for profile in selected:
        if not os.environ.get(profile['key_env']):raise ValueError('Missing key environment variable '+profile['key_env'])
    secrets=[os.environ[p['key_env']] for p in selected]
    keys=lambda p:(p['base_url'],p['model'])
    limiters={keys(p):Limiter(m['settings']) for p in selected}
    existing=phase_rows(phase);rows_by_id={r['request']['id']:r for r in existing}
    for task in spec['schedule']:
        if task['id'] in rows_by_id and rows_by_id[task['id']]['request']!=task:raise ValueError('Observation does not match schedule')
    if len(existing)>len(spec['schedule']):raise ValueError('Unexpected extra observations')
    remaining=[t for t in spec['schedule'] if t['id'] not in rows_by_id]
    print(f'PHASE {name}: {len(existing)}/{len(spec["schedule"])} observations',flush=True)
    done=len(existing)
    atomic(path/'status.json',dict(status='running',phase=name,completed=done,planned=len(spec['schedule']),updated_at=kit.now()))
    with ThreadPoolExecutor(max_workers=m['settings']['workers']) as pool:
        futures=[pool.submit(observation,t,bank[t['probe']],profiles[t['profile']],m,phase,limiters[keys(profiles[t['profile']])],secrets) for t in remaining]
        for future in as_completed(futures):
            row=future.result();done+=1
            if done%10==0 or done==len(spec['schedule']):
                print(f'{name} {done}/{len(spec["schedule"])} last={row["request"]["profile"]}:{row["status"]}',flush=True)
                atomic(path/'status.json',dict(status='running',phase=name,completed=done,planned=len(spec['schedule']),updated_at=kit.now()))
    rows=phase_rows(phase)
    atomic(phase/'complete.json',seal(dict(finished_at=kit.now(),records_sha256=kit.digest(rows),statuses=dict(Counter(r['status'] for r in rows)))))
    return rows


def choose(discovery,probes):
    """Only reference discovery is accepted; target rows are rejected, not ignored."""
    allowed={'gpt4o-a','qwen','llama'}
    if any(r['request']['profile'] not in allowed for r in discovery):raise ValueError('Selection accepts only reference discovery')
    groups=defaultdict(list)
    for r in discovery:
        if r['status']=='ok':groups[(r['request']['probe'],r['request']['profile'])].append(r['text'].strip())
    evidence=[];scores=defaultdict(float)
    for p in probes:
        values=groups[(p['id'],'gpt4o-a')];others=groups[(p['id'],'qwen')]+groups[(p['id'],'llama')]
        if len(values)<2 or len(others)<4:continue
        for answer,count in Counter(values).items():
            frequency=others.count(answer)/len(others)
            if answer!=p['expected'] and count>=2 and frequency<=1/3:
                score=count/len(values)-frequency;scores[p['family']]+=score
                evidence.append(dict(probe=p['id'],family=p['family'],wrong_answer=answer,gpt_count=count,gpt_samples=len(values),alternative_samples=len(others),alternative_frequency=frequency))
    ranked=sorted(scores,key=lambda f:(-scores[f],f))[:8]
    return dict(families=ranked,evidence=evidence,scores=dict(scores),target_observations_used=0)


def run(name):
    import analysis
    path=kit.run_path(name);m=read_sealed(path/'manifest.json')
    if m['code']!=hashes():raise ValueError('Frozen experiment code changed')
    with kit.locked(path):
        try:
            token_rows=run_phase(path,m,'tokenizer',m['tokens'],['gpt4o-a','genesys'],1)
            atomic(path/'tokenizer-analysis.json',seal(analysis.tokenizer(m,token_rows)))
            refs=run_phase(path,m,'discovery',m['discovery'],['gpt4o-a','qwen','llama'],3)
            selection=seal(choose(refs,m['discovery']))
            if (path/'selection.json').exists() and read_sealed(path/'selection.json')!=selection:raise ValueError('Selection changed')
            atomic(path/'selection.json',selection)
            probes=m['perturbations']+[p for f in selection['families'] for p in m['holdout_bank'][f]]
            labels=[p['label'] for p in m['profiles'] if p['label']!='genesys']
            reference_rows=run_phase(path,m,'calibration',probes,labels,m['settings']['replicates'])
            calibration=seal(analysis.calibrate(probes,reference_rows))
            if (path/'calibration.json').exists() and read_sealed(path/'calibration.json')!=calibration:raise ValueError('Calibration changed')
            atomic(path/'calibration.json',calibration)
            print('CALIBRATION',calibration['decision'],flush=True)
            # Target data never enters selection or threshold construction, even if the gate failed.
            target=run_phase(path,m,'target',probes,['genesys'],m['settings']['replicates'])
            atomic(path/'target-analysis.json',seal(analysis.target(probes,reference_rows,target,calibration)))
            analysis.report(path,m)
            first=min(r.get('started_at',r.get('finished_at',kit.now())) for r in target)
            from datetime import datetime
            remaining=600-(time.time()-datetime.fromisoformat(first).timestamp())
            while remaining>0:
                atomic(path/'status.json',dict(status='waiting_temporal',wait_seconds=round(remaining),updated_at=kit.now()))
                time.sleep(min(30,remaining));remaining=600-(time.time()-datetime.fromisoformat(first).timestamp())
            sentinels=[p for p in probes if p['kind']=='choice' and p['variant']==0][:8]
            temporal=run_phase(path,m,'temporal',sentinels,['genesys','gpt4o-a','gpt4o-verify','qwen'],3)
            atomic(path/'temporal-analysis.json',seal(analysis.temporal(sentinels,reference_rows+target,temporal)))
            analysis.report(path,m)
            atomic(path/'status.json',dict(status='completed',phase='all',updated_at=kit.now(),report=str(path/'report.md')))
            print('COMPLETE',path/'report.md',flush=True)
        except BaseException as e:
            atomic(path/'status.json',dict(status='stopped',error_type=type(e).__name__,updated_at=kit.now()))
            raise


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    for name in ['plan','run','status','report']:
        s=sub.add_parser(name);s.add_argument('name')
    args=p.parse_args();path=kit.run_path(args.name)
    if args.cmd=='plan':plan(args.name)
    elif args.cmd=='run':run(args.name)
    elif args.cmd=='status':
        print((path/'status.json').read_text() if (path/'status.json').exists() else 'Planned, not started')
        for phase in ['tokenizer','discovery','calibration','target','temporal']:
            if (path/phase/'plan.json').exists():
                spec=read_sealed(path/phase/'plan.json');rows=phase_rows(path/phase)
                print(phase,len(rows),'/',len(spec['schedule']),dict(Counter(r['status'] for r in rows)))
    else:
        import analysis
        analysis.report(path,read_sealed(path/'manifest.json'))

if __name__=='__main__':main()
