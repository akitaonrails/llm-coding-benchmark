"""Bound repetitive agent activity separately from the cumulative sprint budget."""
import hashlib
import json
import os
import time
from collections import deque
from pathlib import Path

EXCLUDED={'.git','node_modules','vendor','tmp','log','coverage','.bundle','storage','__pycache__'}


def source_digest(root):
    digest=hashlib.sha256()
    for directory,dirs,files in os.walk(root):
        dirs[:]=sorted(d for d in dirs if d not in EXCLUDED and not (Path(directory)/d).is_symlink())
        for name in sorted(files):
            p=Path(directory)/name
            if p.is_symlink() or name.endswith(('.log','.ndjson','.sqlite3','.db','.png','.jpg','.pyc')):
                continue
            try:
                if p.stat().st_size>2_000_000:continue
                digest.update(str(p.relative_to(root)).encode());digest.update(p.read_bytes())
            except (FileNotFoundError,PermissionError):continue
    return digest.hexdigest()


class ProgressWatch:
    def __init__(self, project, transcript, now=None):
        self.project=project; self.transcript=transcript; self.offset=0
        self.last_progress=time.monotonic() if now is None else now
        self.last_scan=0; self.digest=source_digest(project)
        self.history=deque(maxlen=24); self.seen=set()

    def record(self,event):
        part=event.get('part',{})
        state=part.get('state',{})
        if event.get('type')!='tool_use' or state.get('status') not in ('completed','error'):
            return
        call=part.get('callID') or part.get('id')
        if call and call in self.seen:return
        if call:self.seen.add(call)
        payload=[part.get('tool'),state.get('input'),state.get('output'),state.get('error')]
        self.history.append(hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest())

    def check(self,now=None):
        now=time.monotonic() if now is None else now
        if now-self.last_scan>=30:
            current=source_digest(self.project);self.last_scan=now
            if current!=self.digest:
                self.digest=current;self.last_progress=now;self.history.clear()
        if self.transcript.exists():
            with self.transcript.open() as stream:
                stream.seek(self.offset)
                while True:
                    start=stream.tell();line=stream.readline()
                    if not line or not line.endswith('\n'):
                        self.offset=start;break
                    try:self.record(json.loads(line))
                    except (ValueError,TypeError):pass
        quiet=now-self.last_progress
        history=list(self.history)
        if quiet>=120:
            for period in range(1,5):
                count=5 if period==1 else 3
                if len(history)>=period*count and history[-period*count:]==history[-period:]*count:
                    return f'Repeated identical tool input/output cycle (period {period}, {count} repetitions), with no source change for {int(quiet)}s'
        if quiet>=1200:
            return 'No monitored source-content progress for 20 minutes; preserve and review (may include a long legitimate build)'
        return None
