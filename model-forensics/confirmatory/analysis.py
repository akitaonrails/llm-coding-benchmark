"""Descriptive comparisons and an explicit, conservative calibration gate."""
from collections import Counter,defaultdict
import json
import random
import statistics
from pathlib import Path


def distribution(rows,probe,profile,min_samples=4):
    vals=[]
    for r in rows:
        if r['request']['profile']!=profile or r['request']['probe']!=probe['id'] or r['status']!='ok':continue
        text=r['text'].strip()
        if probe['kind']=='choice' and text not in probe['options']:continue
        vals.append(text)
    return ({k:n/len(vals) for k,n in Counter(vals).items()} if len(vals)>=min_samples else {}),len(vals)


def tv(a,b):return sum(abs(a.get(k,0)-b.get(k,0)) for k in a.keys()|b.keys())/2


def bootstrap(values):
    groups=defaultdict(list)
    for block,value in values:groups[block].append(value)
    means=[statistics.mean(v) for v in groups.values()]
    if not means:return None
    r=random.Random(871);sims=sorted(statistics.mean(r.choices(means,k=len(means))) for _ in range(2000))
    return dict(mean=statistics.mean(means),interval95=[sims[49],sims[1949]] if len(means)>=8 else None,blocks=len(means))


def compare(probes,reference,candidate,profile,min_samples=4):
    values=[];details=[];wrong=[]
    for p in probes:
        a,na=distribution(reference,p,'gpt4o-a',min_samples)
        b,nb=distribution(candidate,p,profile,min_samples)
        if not a or not b:
            details.append(dict(probe=p['id'],baseline_samples=na,candidate_samples=nb,available=False));continue
        distance=tv(a,b);values.append((p['block'],distance))
        shared=sum(v*b.get(k,0) for k,v in a.items() if k!=p.get('expected')) if p['kind']=='exact' else None
        if shared is not None:wrong.append((p['block'],shared))
        details.append(dict(probe=p['id'],baseline_samples=na,candidate_samples=nb,available=True,distance=distance,
            baseline_distribution=a,candidate_distribution=b,shared_wrong_answer=shared))
    coverage=len(values)/len(probes) if probes else 0
    return dict(profile=profile,coverage=coverage,adequate=coverage>=.9,distance=bootstrap(values),shared_wrong=bootstrap(wrong),details=details,
        perturbation=perturbation(probes,reference,candidate,profile,min_samples))


def perturbation(probes,reference,candidate,profile,min_samples):
    blocks=defaultdict(dict)
    for p in probes:
        if p['kind']=='choice':blocks[p['block']][p['variant']]=p
    values=[]
    for block,variants in blocks.items():
        if 0 not in variants:continue
        a0,_=distribution(reference,variants[0],'gpt4o-a',min_samples);b0,_=distribution(candidate,variants[0],profile,min_samples)
        if not a0 or not b0:continue
        for v,p in variants.items():
            if v==0:continue
            a,_=distribution(reference,p,'gpt4o-a',min_samples);b,_=distribution(candidate,p,profile,min_samples)
            if not a or not b:continue
            keys=a.keys()|b.keys()|a0.keys()|b0.keys()
            d=sum(abs((a.get(k,0)-a0.get(k,0))-(b.get(k,0)-b0.get(k,0))) for k in keys)/2
            values.append((block,d))
    return bootstrap(values)


def gate(controls):
    positives=['gpt4o-b','gpt4o-system','gpt4o-verify','gpt4o-snapshot']
    negatives=['qwen','qwen-verify','llama']
    if any(not controls[k]['adequate'] or not controls[k]['distance'] or controls[k]['distance']['interval95'] is None for k in positives+negatives):
        return dict(decision='inconclusive_insufficient_control_coverage',threshold=None)
    upper=max(controls[k]['distance']['interval95'][1] for k in positives)
    lower=min(controls[k]['distance']['interval95'][0] for k in negatives)
    if upper>=lower:return dict(decision='inconclusive_controls_overlap',threshold=None,positive_upper=upper,negative_lower=lower)
    return dict(decision='calibrated_separation',threshold=(upper+lower)/2,positive_upper=upper,negative_lower=lower)


def calibrate(probes,rows):
    labels=['gpt4o-b','gpt4o-system','gpt4o-verify','gpt4o-snapshot','qwen','qwen-verify','llama']
    controls={label:compare(probes,rows,rows,label) for label in labels}
    return dict(**gate(controls),controls=controls,genesys_used=False)


def target(probes,reference,rows,calibration):
    comparison=compare(probes,reference,rows,'genesys')
    conclusion='inconclusive'
    if calibration['threshold'] is not None and comparison['adequate'] and comparison['distance'] and comparison['distance']['interval95']:
        lo,hi=comparison['distance']['interval95'];threshold=calibration['threshold']
        if hi<threshold:conclusion='consistent_with_tested_gpt4o_control_envelope'
        elif lo>threshold:conclusion='inconsistent_with_tested_gpt4o_control_envelope'
    return dict(conclusion=conclusion,comparison=comparison,calibration_decision=calibration['decision'],
        limitation='No outcome proves live passthrough or excludes untested wrappers, snapshots, distillation, routing or related weights.')


def tokenizer(m,rows):
    counts={}
    for r in rows:
        usage=r.get('usage')
        if isinstance(usage,dict) and type(usage.get('prompt_tokens')) is int and usage['prompt_tokens']>=0:
            counts[(r['request']['profile'],r['request']['probe'])]=usage['prompt_tokens']
    profiles={}
    for profile in ['genesys','gpt4o-a']:
        models={}
        for encoding,info in m['encodings'].items():
            offset=[counts[(profile,p['id'])]-info['counts'][p['id']] for p in m['tokens'] if p['split']=='offset' and (profile,p['id']) in counts]
            if not offset:models[encoding]=dict(offset=None,available=0);continue
            offset=Counter(offset).most_common(1)[0][0]
            probes=[]
            for p in m['tokens']:
                if p['split']!='holdout' or (profile,p['id']) not in counts:continue
                error=counts[(profile,p['id'])]-info['counts'][p['id']]-offset
                probes.append(dict(probe=p['id'],family=p['family'],residual=error))
            models[encoding]=dict(offset=offset,available=len(probes),expected=768,exact_matches=sum(x['residual']==0 for x in probes),
                match_fraction=sum(x['residual']==0 for x in probes)/len(probes) if probes else None,details=probes)
        profiles[profile]=models
    pairs=[counts[('genesys',p['id'])]-counts[('gpt4o-a',p['id'])] for p in m['tokens'] if ('genesys',p['id']) in counts and ('gpt4o-a',p['id']) in counts]
    return dict(profiles=profiles,paired_available=len(pairs),paired_offset_histogram=dict(Counter(pairs)),
        limitation='Provider-reported counts identify a tokenization/accounting pattern, never model weights or remote dependence.')


def temporal(probes,earlier,later):
    results={}
    for profile in ['genesys','gpt4o-a','gpt4o-verify','qwen']:
        values=[];details=[]
        for p in probes:
            a,na=distribution(earlier,p,profile,2);b,nb=distribution(later,p,profile,2)
            if a and b:
                d=tv(a,b);values.append((p['block'],d));details.append(dict(probe=p['id'],distance=d,earlier_samples=na,later_samples=nb))
        results[profile]=dict(distance=bootstrap(values),details=details)
    return dict(profiles=results,limitation='Same-day short-panel variation includes ordinary sampling noise. No routing conclusion.')


def report(path,m):
    from experiment import read_sealed,atomic,seal,phase_rows
    data={}
    for name in ['tokenizer-analysis','selection','calibration','target-analysis','temporal-analysis']:
        p=path/(name+'.json')
        if p.exists():data[name]=read_sealed(p)
    coverage={}
    for phase in m['phase_order']:
        p=path/phase
        if not (p/'records').exists():continue
        rows=phase_rows(p);by=defaultdict(Counter)
        for row in rows:by[row['request']['profile']][row['status']]+=1
        coverage[phase]={k:dict(v) for k,v in by.items()}
    atomic(path/'report.json',seal(dict(manifest_sha256=m['sha256'],coverage=coverage,analysis=data)))
    lines=['# GPT-4o relationship experiment','',
        'This report concerns similarity to specified GPT-4o configurations. It cannot prove live passthrough or rule out all hidden orchestration.','',
        f"Manifest: `{m['sha256']}`. Sampling: {m['sampling']}. References use OpenRouter snapshot IDs; routing is not independently attested.",'',
        '## Coverage','', '| Phase | Profile | Recorded statuses |','|---|---|---|']
    for phase,profiles in coverage.items():
        for label,statuses in profiles.items():lines.append(f'| {phase} | {label} | {statuses} |')
    if 'tokenizer-analysis' in data:
        lines+=['','## Tokenization','', '| Endpoint | Encoding | Held-out exact matches | Offset |','|---|---|---:|---:|']
        for profile,encodings in data['tokenizer-analysis']['profiles'].items():
            for enc,v in encodings.items():lines.append(f"| {profile} | {enc} | {v.get('exact_matches',0)}/{v['available']} | {v['offset']} |")
        lines+=['','Counts are provider-reported. A match is not an identification of the inference backend.']
    if 'selection' in data:lines+=['','## Reference-only error selection','',f"Selected families: {', '.join(data['selection']['families']) or 'none qualified'}. Genesys observations used: 0."]
    if 'calibration' in data:
        c=data['calibration'];lines+=['','## Calibration','',f"**{c['decision']}**. Threshold: {c['threshold']}.",'',
            '| Control | Distance (lower = more similar) | 95% block interval | Coverage |','|---|---:|---|---:|']
        for label,v in c['controls'].items():
            d=v['distance'];lines.append(f"| {label} | {d['mean'] if d else None} | {d['interval95'] if d else None} | {v['coverage']:.1%} |")
        lines+=['','Intervals describe this panel; they are not probabilities of model identity. If known positives and negatives overlap, classification is disabled.']
    if 'target-analysis' in data:
        t=data['target-analysis'];lines+=['','## Genesys','',f"**{t['conclusion']}**.",'',f"Distance: {t['comparison']['distance']}. Coverage: {t['comparison']['coverage']:.1%}.",'',t['limitation']]
    if 'temporal-analysis' in data:lines+=['','## Temporal repeat','',json.dumps(data['temporal-analysis']['profiles'],indent=2)]
    lines+=['','Per-probe distributions, error agreements, perturbation comparisons, timestamps, metadata and source hashes are in the adjacent JSON artifacts.','']
    (path/'report.md').write_text('\n'.join(lines))
    print(path/'report.md',flush=True)
