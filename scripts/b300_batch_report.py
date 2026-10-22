#!/usr/bin/env python3
"""Refresh evidence-linked progress without inventing grades or quality scores."""
import json
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

def main():
    config=json.loads((ROOT/'config/b300_campaign.json').read_text())
    output=ROOT/'results-v4/_b300_campaign'
    if not (ROOT/'docs').is_dir() or not output.is_dir():
        raise RuntimeError('Do not recreate shielded campaign/report paths')
    ledger_path=output/'ledger.json'
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'models':{}}
    classifications_path = output/'pause-classifications.json'
    classifications = json.loads(classifications_path.read_text()) if classifications_path.exists() else {}
    rows=[]
    for q in config['queue']:
        slug=q['slug'];directory=ROOT/'results-v4'/slug
        results=list((directory/'sprints').glob('*/sprint.result.json'))
        verdicts=sorted((directory/'boundaries').glob('sprint07-*/verdict.json'))
        complete=any(json.loads(p.read_text()).get('eligible') is True for p in verdicts)
        parent=q.get('run_only_if_dnf')
        fallback_not_needed=parent and not any((ROOT/'results-v4'/parent/m).exists() for m in ('DNF','PAUSED'))
        status=('paused for review' if (directory/'PAUSED').exists() else
                'completed' if complete else
                'conditional; not needed yet' if fallback_not_needed else
                'partial' if results else 'pending')
        if (directory/'PAUSED').exists() and slug in classifications:
            status = classifications[slug]['state']
        validation=output/'performance-validation'/f'{slug}.json'
        perf=json.loads(validation.read_text()) if validation.exists() else {}
        row=dict(slug=slug,status=status,sprints=len(results),
                 nudges=len(list((directory/'assistance').glob('*.json'))),
                 sprint_minutes=round(ledger['models'].get(slug,{}).get('sprint_seconds_total',0)/60,2),
                 probe_decode_tokens_per_second=perf.get('decode_tokens_per_second'),
                 final_verdict=str(verdicts[-1].relative_to(ROOT)) if verdicts else None)
        rows.append(row)
    output.mkdir(exist_ok=True)
    (output/'batch-summary.json').write_text(json.dumps({'updated_at':time.time(),'models':rows},indent=2)+'\n')
    lines=['# B300 batch progress','',
           'Probe speed is the latest saved admission measurement and may predate pod revalidation; it is not a coding-quality score. Paused runs retain their work for post-batch review. Follow each evidence link for actual grading and limitations.','',
           '| Model | State | Sprints | Sprint minutes | Probe tok/s | Nudges |',
           '|---|---|---:|---:|---:|---:|']
    for r in rows:
        speed=f"{r['probe_decode_tokens_per_second']:.1f}" if r['probe_decode_tokens_per_second'] is not None else '—'
        link='../'+r['final_verdict'] if r['final_verdict'] else '../results-v4/'+r['slug']
        lines.append(f"| [{r['slug']}]({link}) | {r['status']} | {r['sprints']}/7 | {r['sprint_minutes']:.2f} | {speed} | {r['nudges']} |")
    docs=ROOT/'docs'
    if not docs.is_dir():raise RuntimeError('Do not recreate shielded documentation')
    (docs/'b300-batch-status.md').write_text('\n'.join(lines)+'\n')
    print('Batch progress report refreshed')

if __name__=='__main__':main()
