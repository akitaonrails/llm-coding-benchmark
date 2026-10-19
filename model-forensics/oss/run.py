#!/usr/bin/env python3
"""Gated gpt-oss output comparison, isolated from coding benchmarks."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'confirmatory'))
import experiment as e
import client
import oss_probes
import oss_analysis as a


def profiles():
    def ref(label,model,provider=None,wrapper='plain'):
        params={'reasoning':{'effort':'low'},'provider':{'allow_fallbacks':False,'require_parameters':True}}
        if provider:params['provider']['order']=[provider]
        return dict(label=label,model=model,base_url='https://openrouter.ai/api/v1',key_env='OPENROUTER_API_KEY',wrapper=wrapper,parameters=params)
    return [ref('oss120','openai/gpt-oss-120b','groq'),
        ref('oss120-provider','openai/gpt-oss-120b','deepinfra/bf16'),
        ref('oss120-system','openai/gpt-oss-120b','groq','system'),
        ref('oss120-verify','openai/gpt-oss-120b','groq','verify'),
        ref('oss20','openai/gpt-oss-20b','deepinfra/bf16'),
        ref('glm','z-ai/glm-5.3','relace'),ref('kimi','moonshotai/kimi-k3','relace'),
        dict(label='genesys',model='genesys-pi-house',base_url='https://api.lua.vision/v1',key_env='LUA_API_KEY',wrapper='plain')]


def sources():
    files=[ROOT/f for f in ['run.py','client.py','oss_probes.py','oss_analysis.py','PROTOCOL.md']]
    files += [ROOT.parent/f for f in ['kit.py','probes.py','confirmatory/experiment.py','confirmatory/panel.py']]
    return {str(p.relative_to(ROOT.parent)):p for p in files}


def hashes():return {k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in sources().items()}


def preflight(name):
    path=e.kit.run_path(name);path.mkdir(parents=True,exist_ok=False)
    def one(p):
        if not os.environ.get(p['key_env']):raise ValueError('Missing '+p['key_env'])
        r=client.call(p,[{'role':'user','content':'Return only the letter A.'}],4096,120,[os.environ[p['key_env']]])
        e.atomic(path/(p['label']+'.json'),e.seal(dict(profile=p,result=r)))
        return dict(profile=p['label'],status=r['status'],provider=r.get('provider'),text=r.get('text'),error=r.get('error'))
    # No further target collection needed for routing preflight.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(one,[p for p in profiles() if p['label'] in ['oss120','oss120-provider','oss20','glm','kimi']]):
            print(json.dumps(result,ensure_ascii=False),flush=True)


def freeze(name):
    path=e.kit.run_path(name);path.mkdir(parents=True,exist_ok=False)
    m=e.seal(dict(name=name,created_at=e.kit.now(),code=hashes(),python=sys.version,
        tiktoken=importlib.metadata.version('tiktoken'),profiles=profiles(),probes=oss_probes.build(),
        max_tokens=4096,timeout_seconds=120,sampling='temperature omitted; reference reasoning low',
        settings=dict(workers=8,endpoint_concurrency=2,min_interval_seconds=.5,rate_cooldown_seconds=60),
        discovery_repeats=2,validation_repeats=6,target_repeats=8,max_physical_calls=1664))
    e.atomic(path/'manifest.json',m)
    for k,p in sources().items():
        target=path/'source'/k;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
    print('Frozen '+name,flush=True)
    return m


def report(path,status,selection,calibration=None,target=None):
    result=dict(status=status,finished_at=e.kit.now(),selection=selection,calibration=calibration,target=target)
    e.atomic(path/'report.json',e.seal(result))
    lines=['# gpt-oss output investigation','',f'Status: **{status}**.', '',
        f"Selected {len(selection['selected'])} independent signature blocks from reference-only discovery.",
        '','This study compares answers, repeated errors, copying behavior and response preferences. Token counts are not classification evidence.']
    if calibration:
        lines += ['',f"Independent validation: **{calibration['decision']}**.",'', '| Reference control | Mean answer-distribution distance | 95% interval | Coverage |','|---|---:|---|---:|']
        for k,c in calibration['controls'].items():
            d=c['distance'];lines.append(f"| {k} | {d['mean'] if d else 'unavailable'} | {d['interval95'] if d else 'unavailable'} | {c['coverage']:.1%} |")
    if target:
        c=target['comparison'];lines += ['',f"Genesys: **{target['decision']}**.",f"Distance: {c['distance']}; coverage: {c['coverage']:.1%}."]
    else:lines += ['','No Genesys batch was collected: the reference gate did not establish a validated signature. This says the assay is not sufficiently discriminative; it does not exclude gpt-oss ancestry.']
    lines += ['','Detailed distributions and shared wrong answers are in report.json. Raw calls, sealed observations and schedules are retained in each phase.', '',
        'Matching this envelope supports behavioral similarity to the tested configuration. Falling outside weakens an unmodified or lightly wrapped 120B hypothesis. Neither result identifies training ancestry, proves ownership, or excludes substantial fine-tuning/distillation. The 20B comparison is exploratory.',
        '', 'Intervals resample selected prompt blocks and describe this panel, not all possible prompts. Fresh validation responses are independent of discovery; the prompt bank itself is fixed.']
    (path/'report.md').write_text('\n'.join(lines)+'\n')
    e.atomic(path/'status.json',dict(status=status,updated_at=e.kit.now(),report='report.md'))


def run(name):
    path=e.kit.run_path(name);m=e.read_sealed(path/'manifest.json')
    if m['code']!=hashes():raise ValueError('Source changed after freeze; use a new run')
    e.http_call=client.call
    labels=[p['label'] for p in m['profiles'] if p['label']!='genesys']
    rows=e.run_phase(path,m,'discovery',m['probes'],labels,m['discovery_repeats'])
    selection=a.select(m['probes'],rows);e.atomic(path/'selection.json',e.seal(selection))
    if selection['decision']!='validate':
        report(path,'completed_no_validated_signature',selection);return
    ids={c['probe'] for c in selection['selected']};probes=[p for p in m['probes'] if p['id'] in ids]
    rows=e.run_phase(path,m,'validation',probes,labels,m['validation_repeats'])
    calibration=a.validate(probes,rows);e.atomic(path/'calibration.json',e.seal(calibration))
    if calibration['decision']!='pass':
        report(path,'completed_validation_failed',selection,calibration);return
    target_rows=e.run_phase(path,m,'target',probes,['genesys'],m['target_repeats'])
    report(path,'completed',selection,calibration,a.target(probes,rows,target_rows,calibration))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['preflight','freeze','run']);p.add_argument('name');args=p.parse_args()
    {'preflight':preflight,'freeze':freeze,'run':run}[args.command](args.name)
