"""Archive pause/control records for an explicitly approved infrastructure retry."""
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent


def main():
    slug=sys.argv[1]
    approved=json.loads((ROOT/'results-v4/_b300_campaign/recovery-20261017.json').read_text())
    entry=next(e for e in approved['models'] if e['slug']==slug)
    model=ROOT/'results-v4'/slug
    archive=model/'pause-checkpoints'/f'infrastructure-recovery-{time.time_ns()}'
    archive.mkdir(parents=True)
    for name in ('PAUSED','DNF','RESUME.md','THROUGHPUT_SKIP.md','TIME_GUARD.md'):
        p=model/name
        if p.exists():p.rename(archive/name)
    evidence=ROOT/'results-v4/_b300_campaign/migration-20261017'
    tuning=evidence/f'new-pod-tuning-{slug}.json'
    if tuning.exists():
        previous=json.loads(tuning.read_text())
        tuning.rename(archive/tuning.name)
        if not entry.get('boundary'):
            config_path=ROOT/'config/b300_campaign.json'
            config=json.loads(config_path.read_text())
            selected=next(q for q in config['queue'] if q['slug']==slug)
            selected['serve_args']=previous['trials'][0]['serve_args']
            config_path.write_text(json.dumps(config,indent=2)+'\n')
    if entry.get('serving_override'):
        config_path=ROOT/'config/b300_campaign.json'
        config=json.loads(config_path.read_text())
        selected=next(q for q in config['queue'] if q['slug']==slug)
        selected.update(entry['serving_override'])
        config_path.write_text(json.dumps(config,indent=2)+'\n')
    (archive/'recovery.json').write_text(json.dumps(dict(time=time.time(),entry=entry,
        preserves='All source, transcripts, sessions, previous admission and cumulative sprint budget'),indent=2)+'\n')
    print(f'{slug}: archived pause markers; preserved all sprint state and cumulative budget')


if __name__=='__main__':main()
