#!/usr/bin/env python3
"""Bounded per-model tuning ledger and evidence-based admission to timed sprints."""
import argparse,json,statistics,subprocess,sys,time
from pathlib import Path
import run_b300_campaign as campaign

def path(slug):
    return campaign.LEDGER_DIR/'tuning'/f'{slug}.json'

def save(slug,state):
    p=path(slug);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(p)

def update_runbook():
    doc=campaign.REPO/'docs/runpod-b300-openweights-runbook.md'
    if not doc.exists():return  # Never recreate documentation while a sprint shield is active.
    start='<!-- b300-measured-optimizations:start -->';end='<!-- b300-measured-optimizations:end -->'
    lines=[start,'### Measured optimization outcomes','',
           'Rates are warm single-request decode measurements, not benchmark quality scores. Exact arguments, errors and raw evidence are linked below.','',
           '| Model | Configuration | Decode tok/s | Tool preflight | Outcome |',
           '|---|---|---:|---|---|']
    for ledger in sorted((campaign.LEDGER_DIR/'tuning').glob('*.json')):
        state=json.loads(ledger.read_text());slug=state['slug']
        for r in state['rounds']:
            rate=r.get('decode_tokens_per_second');rate=f'{rate:.2f}' if rate is not None else '—'
            outcome=('Running' if not r.get('finished_at') else 'Accepted' if r.get('passed') else 'Failed validation' if r.get('error') else 'Below throughput threshold')
            tool='Passed' if r.get('tool_preflight_passed') else 'Not passed/recorded'
            link='../'+str(ledger.relative_to(campaign.REPO))
            lines.append(f'| [{slug}]({link}) | {r["label"]} | {rate} | {tool} | {outcome} |')
    lines += ['', 'A slower or incompatible attempt is retained; successful flags are not generalized to other architectures without measurement.',end]
    section='\n'.join(lines)
    text=doc.read_text()
    if start in text:
        before,rest=text.split(start,1);_,after=rest.split(end,1);text=before+section+after
    else:text+='\n\n'+section+'\n'
    doc.write_text(text)

def policy():return campaign.CAMP['optimization_policy']

def begin(slug,label):
    p=path(slug);now=time.time()
    state=json.loads(p.read_text()) if p.exists() else {'slug':slug,'started_at':now,'rounds':[]}
    if len(state['rounds'])>=policy()['max_configurations_per_model']:
        raise RuntimeError('Configuration limit reached')
    if now-state['started_at']>=policy()['max_tuning_wall_seconds']:
        raise RuntimeError('Tuning wall-time limit reached')
    if state['rounds'] and state['rounds'][-1].get('finished_at') is None:
        raise RuntimeError('Previous tuning round is still active')
    model=next(q for q in campaign.CAMP['queue'] if q['slug']==slug)
    state['rounds'].append({'label':label,'started_at':now,'serving_fingerprint':campaign.serving_fingerprint(slug),
                           'serve_args':model['serve_args'],'checkpoint':model['hf_repo']})
    save(slug,state)
    update_runbook()
    return state

def probe_rate(data):
    rows=data.get('records',[])
    if len(rows)!=3:raise ValueError('Need one cold and two warm probe records')
    rates=[]
    for row in rows:
        if row.get('usage',{}).get('completion_tokens')!=256:raise ValueError('Probe output length changed')
        elapsed=row['elapsed_seconds'];first=row['first_token_seconds']
        if first is None or elapsed<=first:raise ValueError('Invalid probe timings')
        rates.append(255/(elapsed-first))
    return statistics.median(rates[1:])

def finish(slug,probe=None,preflight=None,error=None):
    state=json.loads(path(slug).read_text());r=state['rounds'][-1]
    if r.get('finished_at'):raise RuntimeError('Round already finished')
    now=time.time();r['finished_at']=now;r['evidence']=[]
    if probe:
        data=json.loads(Path(probe).read_text())
        if data['slug']!=slug:raise ValueError('Probe belongs to another model')
        r['evidence'].append(str(Path(probe).resolve().relative_to(campaign.REPO)))
        try:r['decode_tokens_per_second']=probe_rate(data)
        except (ValueError,KeyError,TypeError):error=error or 'Incomplete or invalid throughput probe'
    r['tool_preflight_passed']=False
    if preflight:
        data=json.loads(Path(preflight).read_text())
        if data['slug']!=slug:raise ValueError('Preflight belongs to another model')
        r['tool_preflight_passed']=data.get('passed') is True
        r['evidence'].append(str(Path(preflight).resolve().relative_to(campaign.REPO)))
    r['error']=error
    r['passed']=(not error and r.get('decode_tokens_per_second',0)>=policy()['minimum_decode_tokens_per_second']
                 and r['tool_preflight_passed'] and now-state['started_at']<=policy()['max_tuning_wall_seconds']
                 and r['serving_fingerprint']==campaign.serving_fingerprint(slug))
    state['tuning_wall_seconds']=now-state['started_at']
    state['tuning_wall_cost_usd']=campaign.usd(state['tuning_wall_seconds'])
    save(slug,state)
    update_runbook()
    if r['passed']:
        out=campaign.LEDGER_DIR/'performance-validation'/f'{slug}.json';out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(r,indent=2)+'\n')
    return r

def skip(slug,reason):
    state=json.loads(path(slug).read_text());state['status']='paused_serving_throughput';state['reason']=reason;save(slug,state)
    update_runbook()
    out=campaign.OUT/slug;out.mkdir(parents=True,exist_ok=True)
    (out/'THROUGHPUT_SKIP.md').write_text(f'# Skipped: serving throughput\n\n{reason}\n\nThis is an infrastructure eligibility result, not a model-quality failure. No ranked score.\n\nEvidence: ../_b300_campaign/tuning/{slug}.json\n')
    (out/'DNF').write_text('INFRASTRUCTURE THROUGHPUT SKIP: '+reason+'\n')
    validation=campaign.LEDGER_DIR/'performance-validation'/f'{slug}.json'
    if validation.exists():
        d=json.loads(validation.read_text());d['passed']=False;d['revoked_reason']=reason;validation.write_text(json.dumps(d,indent=2)+'\n')
    from b300_pause import checkpoint
    checkpoint(slug, reason)
    return state

def measure(slug):
    """Bound the complete readiness, tool-preflight and throughput measurement tree."""
    state=json.loads(path(slug).read_text());r=state['rounds'][-1]
    if r.get('finished_at'):raise RuntimeError('No active tuning round')
    deadline=state['started_at']+policy()['max_tuning_wall_seconds']
    evidence_dir=campaign.LEDGER_DIR/'migration-20261017'
    marker=time.time();error=None
    commands=[
        [sys.executable,str(campaign.REPO/'scripts/b300_start_sprint.py'),slug,'--preflight-only',
         '--ready-timeout',str(max(1,min(900,int(deadline-time.time()))))],
        [sys.executable,str(campaign.REPO/'scripts/b300_perf_probe.py'),slug,'--label',r['label']]]
    log=path(slug).with_name(f'{slug}-{time.time_ns()}-measurement.log')
    with log.open('w') as output:
        for command in commands:
            remaining=deadline-time.time()
            if remaining<=0:
                error='Tuning wall-time limit reached';break
            proc=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                rc=proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                campaign.stop_sprint_tree(proc,grace=5)
                error='Tuning wall-time limit reached';break
            if rc:
                error=f'Candidate measurement failed with exit {rc}';break
    def latest(pattern):
        files=[p for p in evidence_dir.glob(pattern) if p.stat().st_mtime>=marker]
        return str(max(files,key=lambda p:p.stat().st_mtime)) if files else None
    result=finish(slug,latest(f'perf-{slug}-{r["label"]}-*.json'),latest(f'preflight-{slug}-*.json'),error)
    if not result['passed'] and (len(state['rounds'])>=policy()['max_configurations_per_model'] or time.time()>=deadline):
        skip(slug,error or f'No validated configuration reached {policy()["minimum_decode_tokens_per_second"]} decoded tokens/sec within the tuning limits')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('slug');g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--begin');g.add_argument('--finish',action='store_true');g.add_argument('--skip');g.add_argument('--measure',action='store_true')
    ap.add_argument('--probe');ap.add_argument('--preflight');ap.add_argument('--error');a=ap.parse_args()
    if a.begin:r=begin(a.slug,a.begin)
    elif a.skip:r=skip(a.slug,a.skip)
    elif a.measure:r=measure(a.slug)
    else:r=finish(a.slug,a.probe,a.preflight,a.error)
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
