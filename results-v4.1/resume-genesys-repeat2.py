import json, subprocess, sys
from pathlib import Path
root=Path.cwd()
sys.path.insert(0,str(root/'scripts'))
from run_v41_frontier import write_json
p=root/'results-v4.1/genesys-repeat2-queue.json'
d=json.loads(p.read_text());d.pop('error',None);d['status']='running';write_json(p,d)
r=subprocess.run([sys.executable,str(root/'scripts/run_v41_frontier_wave.py'),'--models','genesys_repeat2','--cranelift-memory-mb','32768'])
d['status']='completed' if r.returncode==0 else 'error'
if r.returncode:d['error']='Frontier queue failed; inspect frontier/genesys-repeat2-queue.json'
write_json(p,d)
