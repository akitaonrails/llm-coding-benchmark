"""Reference-only output signature discovery, validation, then target matching."""
from collections import Counter,defaultdict
import json
import random
import re
import statistics

POSITIVES=['oss120-provider','oss120-system','oss120-verify']
NEGATIVES=['glm','kimi']


def normalize(text):
    text=text.strip()
    fence=re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```',text,re.S|re.I)
    if fence:text=fence.group(1).strip()
    try:
        value=json.loads(text)
        if isinstance(value,str):return value
    except ValueError:pass
    return text


def dist(rows,p,label,min_samples=2):
    values=[normalize(r['text']) for r in rows if r['status']=='ok' and r['request']['probe']==p['id'] and r['request']['profile']==label]
    if p['kind']=='choice':values=[v for v in values if v in p['options']]
    if len(values)<min_samples:return {},len(values)
    return {k:n/len(values) for k,n in Counter(values).items()},len(values)


def tv(a,b):return sum(abs(a.get(k,0)-b.get(k,0)) for k in a.keys()|b.keys())/2


def select(probes,rows):
    if any(r['request']['profile']=='genesys' for r in rows):raise ValueError('Target data forbidden in selection')
    candidates=[]
    for p in probes:
        if p['family']=='copy-control':continue
        base,n=dist(rows,p,'oss120')
        if not base:continue
        controls={k:dist(rows,p,k)[0] for k in POSITIVES+NEGATIVES}
        if any(not d for d in controls.values()):continue
        positive=max(tv(base,controls[k]) for k in POSITIVES)
        negative=min(tv(base,controls[k]) for k in NEGATIVES)
        if positive<=.25 and negative-positive>=.5:
            candidates.append(dict(probe=p['id'],block=p['block'],family=p['family'],positive_max=positive,negative_min=negative,margin=negative-positive,baseline=base))
    # One strongest variant per block; do not count choice-order twins as independent.
    chosen=[];seen=set()
    for c in sorted(candidates,key=lambda x:(-x['margin'],x['probe'])):
        if c['block'] not in seen:chosen.append(c);seen.add(c['block'])
        if len(chosen)==16:break
    return dict(selected=chosen,eligible=len(candidates),decision='validate' if len(chosen)>=8 else 'stop_insufficient_distinctive_signatures',target_used=False)


def interval(values):
    if len(values)<8:return None
    rng=random.Random(9915);samples=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(2000))
    return dict(mean=statistics.mean(values),interval95=[samples[49],samples[1949]])


def compare(probes,reference,rows,label):
    details=[];values=[]
    for p in probes:
        base,nb=dist(reference,p,'oss120',4);other,no=dist(rows,p,label,4)
        if not base or not other:
            details.append(dict(probe=p['id'],available=False,base_samples=nb,other_samples=no));continue
        d=tv(base,other);values.append(d)
        wrong=sum(v*other.get(k,0) for k,v in base.items() if k!=p.get('expected')) if p['kind']=='exact' else None
        details.append(dict(probe=p['id'],available=True,distance=d,base=base,other=other,base_samples=nb,other_samples=no,same_wrong_answer=wrong))
    return dict(profile=label,coverage=len(values)/len(probes) if probes else 0,distance=interval(values),details=details)


def validate(probes,rows):
    if any(r['request']['profile']=='genesys' for r in rows):raise ValueError('Target data forbidden in calibration')
    controls={k:compare(probes,rows,rows,k) for k in POSITIVES+NEGATIVES+['oss20']}
    if any(controls[k]['coverage']<.9 or not controls[k]['distance'] for k in POSITIVES+NEGATIVES):return dict(decision='stop_insufficient_coverage',threshold=None,controls=controls)
    upper=max(controls[k]['distance']['interval95'][1] for k in POSITIVES)
    lower=min(controls[k]['distance']['interval95'][0] for k in NEGATIVES)
    return dict(decision='pass' if upper<lower else 'stop_controls_overlap',threshold=(upper+lower)/2 if upper<lower else None,positive_upper=upper,negative_lower=lower,controls=controls)


def target(probes,reference,rows,calibration):
    c=compare(probes,reference,rows,'genesys');decision='inconclusive'
    if calibration['decision']=='pass' and c['coverage']>=.9 and c['distance']:
        lo,hi=c['distance']['interval95'];threshold=calibration['threshold']
        if hi<threshold:decision='matches_tested_oss120_behavioral_envelope'
        elif lo>threshold:decision='outside_tested_oss120_behavioral_envelope'
    return dict(decision=decision,comparison=c,limitation='Not a probability of ancestry. Does not rule out substantial fine-tuning/distillation or an untested base.')
