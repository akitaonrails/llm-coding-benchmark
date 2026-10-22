"""Small transport helpers for the campaign's PTY-only RunPod SSH proxy."""
from __future__ import annotations
import base64
import subprocess
import sys
import time
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def execute(command: str, timeout: int = 60) -> str:
    result = subprocess.run(
        [sys.executable, str(REPO / 'scripts/pod_exec.py'), '--timeout', str(timeout), command],
        capture_output=True, text=True, timeout=timeout + 65)
    if result.returncode:
        # Commands can carry credentials. Never echo command or partial PTY output.
        combined=result.stderr+result.stdout
        category=next((word for word in ('EOF','TIMEOUT','Permission denied','No space left','Connection closed','not running') if word in combined),'unclassified transport/command failure')
        raise RuntimeError(f'RunPod command failed (exit {result.returncode}; {category})')
    return result.stdout


def upload(data: bytes, path: str, mode: str = '600') -> None:
    # Whole-file transfer is idempotent: restart from truncation, never append a
    # retried chunk to a possibly successful previous chunk.
    for attempt in range(3):
        try:
            return _upload_once(data, path, mode)
        except (RuntimeError, subprocess.TimeoutExpired):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def _upload_once(data: bytes, path: str, mode: str = '600') -> None:
    # Shell-safe fixed paths only, with chunks below the PTY canonical line limit.
    if not path.startswith('/root/') or any(c not in '/-_.0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' for c in path):
        raise ValueError('Expected a simple absolute /root/ path')
    if mode not in ('600', '700'):
        raise ValueError('Unsupported mode')
    with tempfile.NamedTemporaryFile(prefix='b300-upload-') as source:
        source.write(data)
        source.flush()
        result = subprocess.run([sys.executable, str(REPO/'scripts/pod_exec.py'),
            '--upload', source.name, '--destination', path, '--timeout', '30'],
            capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise RuntimeError(f'RunPod atomic upload failed (exit {result.returncode})')
    if mode == '700':
        execute(f'chmod 700 {path}')
