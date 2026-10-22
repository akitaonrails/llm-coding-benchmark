import json,subprocess,ctypes
from pathlib import Path
libs=list(Path('/root/.cache/flashinfer/0.7.0.post1/103a/cached_ops').glob('*/*.so'))
def missing():
 return {str(p):[s.strip() for s in subprocess.run(['ldd',str(p)],capture_output=True,text=True).stdout.splitlines() if 'not found' in s] for p in libs}
before=missing()
p=Path('/etc/ld.so.conf.d/b300-cuda12-runtime.conf')
assert Path('/usr/local/cuda-12.9/lib64/libcudart.so.12').exists()
p.write_text('/usr/local/cuda-12.9/lib64\n')
subprocess.run(['ldconfig'],check=True,capture_output=True)
after=missing()
ctypes.CDLL('libcudart.so.12')
result={'before_missing':{k:v for k,v in before.items() if v},'after_missing':{k:v for k,v in after.items() if v},'cuda12_load_passed':True,'loader_config':str(p)}
Path('/root/logs/cuda12-loader-repair.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
