#!/usr/bin/env python3
"""Record a resumable B300 pause without deleting workspace or inference files."""
import argparse,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def checkpoint(slug,reason):
    if '/' in slug or slug.startswith('.'):raise ValueError('Invalid model slug')
    campaign=json.loads((ROOT/'config/b300_campaign.json').read_text())
    model=next(q for q in campaign['queue'] if q['slug']==slug)
    out=ROOT/'results-v4'/slug;out.mkdir(parents=True,exist_ok=True)
    control=ROOT/'results-v4/_b300_campaign'
    ledger=json.loads((control/'ledger.json').read_text()) if (control/'ledger.json').exists() else {}
    tuning=control/'tuning'/f'{slug}.json'
    revisions=control/'migration-20261017/checkpoints.json'
    pinned=json.loads(revisions.read_text()) if revisions.exists() else None
    sprints=[];sessions=set()
    for directory in sorted((out/'sprints').glob('*')):
        if not directory.is_dir():continue
        result=directory/'sprint.result.json'
        summary={'sprint':directory.name,'result_path':str(result.relative_to(ROOT)) if result.exists() else None}
        if result.exists():
            data=json.loads(result.read_text());summary['exit_code']=data.get('exit_code');summary['stall_aborted']=data.get('stall_aborted')
        for log in directory.glob('*.ndjson'):
            for line in log.open():
                try:event=json.loads(line)
                except ValueError:continue
                sid=event.get('sessionID') or event.get('session_id')
                if isinstance(sid,str) and sid.startswith('ses_') and sid.replace('_','').isalnum():sessions.add(sid)
        sprints.append(summary)
    archive=out/'pause-checkpoints'/str(time.time_ns());archive.mkdir(parents=True,mode=0o700)
    exports=[]
    for sid in sorted(sessions):
        destination=archive/f'{sid}.json'
        with destination.open('w') as f:
            try:
                result=subprocess.run(['opencode','export',sid],stdout=f,stderr=subprocess.DEVNULL,timeout=60)
                status='exported' if result.returncode==0 and destination.stat().st_size else 'export_failed'
            except (OSError,subprocess.TimeoutExpired):status='export_failed'
        destination.chmod(0o600);exports.append({'session_id':sid,'path':str(destination.relative_to(ROOT)),'status':status})
    workspace=out/'project';git={}
    if (workspace/'.git').exists():
        for name,args in [('head',['rev-parse','HEAD']),('status',['status','--porcelain'])]:
            r=subprocess.run(['git',*args],cwd=workspace,capture_output=True,text=True,timeout=30);git[name]=r.stdout
    state={'status':'paused_pending_batch_review','reason':reason,'recorded_at':time.time(),
           'model':model,'checkpoint_revision_manifest':pinned,'workspace':str(workspace.relative_to(ROOT)),'workspace_exists':workspace.exists(),
           'sprints':sprints,'sessions':exports,'git':git,'ledger':ledger.get('models',{}).get(slug,{}),
           'tuning':json.loads(tuning.read_text()) if tuning.exists() else None,
           'remote_retention':{'weights':'/root/models/'+model['local_dir'],'retain':['model-specific caches','temporary files required to resume','server logs and launch state; archive locally before replacing shared state'],
                               'weights_policy':'May delete downloaded weights only when space is needed, after verifying and recording the exact repository and immutable revision. Preserve execution state and caches.',
                               'gpu_process':'May stop owned inference process after archiving; KV cache is transient and will be rebuilt.'},
           'resume_checklist':['Review all models after batch before selecting resumptions.',
             'Archive remote launch state/logs locally before loading another model; preserve execution state/caches; weights alone may be removed if space is needed and an immutable revision is recorded.',
             'Restore serving configuration from this checkpoint and verify API/tool preflight.',
             'Verify session export succeeded; retain local OpenCode session store. Do not delete failed export evidence.',
             'Determine whether current sprint ended or was interrupted; preserve existing logs before continuation.',
             'Do not blindly rerun standard launcher: it skips existing sprint.result.json and DNF markers.',
             'Verify grading/injection boundary records before advancing sprint. Never repeat completed injections.',
             'Record any additional authorized budget separately; keep original attempt time, costs and pause artifacts.']}
    manifest=archive/'state.json';manifest.write_text(json.dumps(state,indent=2)+'\n');manifest.chmod(0o600)
    (out/'PAUSED').write_text('Pending post-batch review: '+reason+'\nCheckpoint: '+str(manifest.relative_to(ROOT))+'\n')
    (out/'RESUME.md').write_text('# Paused pending batch review\n\n'+reason+'\n\nCheckpoint: `'+str(manifest.relative_to(ROOT))+'`\n\n'+ '\n'.join('- '+x for x in state['resume_checklist'])+'\n\nPreserve the entire workspace, temporary files, session data and remote execution state/caches. Downloaded weights alone may be removed for space after recording an immutable revision. DNF is a queue-control marker for this budget, not a final abandonment decision.\n')
    return manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('slug');ap.add_argument('--reason',default='Campaign guard reached');ap.add_argument('--watch-runner',type=int);a=ap.parse_args()
    if a.watch_runner:
        import run_b300_campaign as c
        ident=c.process_identity(a.watch_runner)
        if not ident:raise RuntimeError('Runner not live')
        while True:
            now=c.process_identity(a.watch_runner)
            if not now or now[1]!=ident[1] or now[2]=='Z':break
            time.sleep(5)
        # The supervisor records the guard after its runner exits/restores the shield.
        for _ in range(24):
            out=ROOT/'results-v4'/a.slug
            if (out/'DNF').exists():
                if not (out/'PAUSED').exists():print(checkpoint(a.slug,a.reason))
                return
            time.sleep(5)
        return  # Normal sprint completion is not a paused model.
    print(checkpoint(a.slug,a.reason))
if __name__=='__main__':main()
