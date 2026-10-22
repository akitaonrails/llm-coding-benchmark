"""One ten-minute ordinary-defect nudge, charged to the original sprint budget."""
import json
import subprocess
import sys
import time
from pathlib import Path
import run_b300_campaign as campaign
from b300_progress import ProgressWatch
from b300_model_plan import SPRINTS


def main():
    slug,boundary=sys.argv[1:3]
    root=campaign.OUT/slug
    records=root/'assistance'
    if len(list(records.glob('*.json')))>=2:
        print('Assistance limit reached; preserving pause')
        return 2
    reviews=sorted((root/'boundaries').glob(f'sprint{boundary}-*'))
    source=reviews[-1]/'assistance.json'
    request=json.loads(source.read_text())
    if request.get('category')!='ordinary_minor_defect' or not 1<=len(request.get('prompt',''))<=1200:
        raise ValueError('No bounded ordinary-defect nudge authorized by reviewer')
    ledger=campaign.load_ledger();entry=campaign.entry(ledger,slug)
    remaining=campaign.current_budget()-entry['sprint_seconds_total']
    if remaining<=0:return 2
    tag=f'repair{boundary}_{time.time_ns()}'
    (root/'repairs').mkdir(exist_ok=True)
    records.mkdir(exist_ok=True)
    prompt_file=records/f'{tag}.json'
    prompt_file.write_text(json.dumps(dict(sprint=tag,classification='assisted',source=str(source),
        prompt=request['prompt'],issued_at=time.time(),timing='Dedicated repair, capped at ten minutes and charged to cumulative sprint budget'),indent=2)+'\n')
    command=[sys.executable,str(campaign.REPO/'scripts/run_v4_sprint.py'),'--model',slug,
             '--sprint',SPRINTS[int(boundary)-1],'--repair-prompt',str(prompt_file),'--repair-tag',tag]
    start=time.time();proc=subprocess.Popen(command,start_new_session=True)
    watch=ProgressWatch(root/'project',root/'repairs'/tag/f'{tag}.ndjson')
    reason=None
    try:
        while proc.poll() is None:
            reason=watch.check()
            if reason or time.time()-start>=min(600,remaining):
                reason=reason or 'Ten-minute repair or remaining cumulative budget exhausted'
                campaign.stop_sprint_tree(proc);break
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:pass
    finally:
        if proc.poll() is None:campaign.stop_sprint_tree(proc)
        elapsed=time.time()-start
        entry['sprint_seconds_total']+=elapsed
        entry['sprints'][tag]=dict(seconds=round(elapsed),assisted=True,reason=reason,exit=proc.returncode)
        entry['model_time_cost_usd']=campaign.usd(entry['sprint_seconds_total']+entry.get('prior_attempt_sprint_seconds',0))
        campaign.save_ledger(ledger)
        (root/'repairs'/f'{tag}-controller.json').write_text(json.dumps(entry['sprints'][tag],indent=2)+'\n')
    return 0 if proc.returncode==0 and reason is None else 2


if __name__=='__main__':raise SystemExit(main())
