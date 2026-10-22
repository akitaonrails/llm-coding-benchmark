"""Record bounded reviewer-requested nudges without changing the sprint budget."""
import json
import time
from pathlib import Path


def consume(model_root: Path, sprint: str):
    previous=int(sprint[:2])-1
    if previous < 1:
        return None
    records=model_root/'assistance'
    used=list(records.glob('*.json')) if records.exists() else []
    if len(used)>=2 or any(json.loads(p.read_text()).get('sprint')==sprint for p in used):
        return None
    boundaries=sorted((model_root/'boundaries').glob(f'sprint{previous:02d}-*'))
    if not boundaries:
        return None
    source=boundaries[-1]/'assistance.json'
    verdict=boundaries[-1]/'verdict.json'
    if not source.exists() or not verdict.exists() or not json.loads(verdict.read_text()).get('eligible'):
        return None
    request=json.loads(source.read_text())
    prompt=request.get('prompt','')
    if request.get('category')!='ordinary_minor_defect' or not isinstance(prompt,str) or not 1<=len(prompt)<=1200:
        return None
    record=dict(sprint=sprint,prompt=prompt,source=str(source),issued_at=time.time(),
                classification='assisted',timing='Included in this sprint and existing cumulative four-hour budget; no causal extra-time estimate')
    records.mkdir(exist_ok=True)
    (records/f'{time.time_ns()}.json').write_text(json.dumps(record,indent=2)+'\n')
    return record
