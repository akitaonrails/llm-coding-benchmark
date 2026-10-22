#!/usr/bin/env python3
"""Execute a command on the RunPod pod via the ssh.runpod.io proxy.

The RunPod SSH proxy IGNORES the remote-command field and drops you into an
interactive root shell (it also refuses PTY-less sessions), so plain
`ssh pod 'cmd'` executes nothing. This helper drives the interactive shell
with pexpect:

  1. wait for the root prompt (after the MOTD banner)
  2. turn off terminal echo + bash bracketed-paste (a pasted long line with a
     newline is otherwise quoted, not executed)
  3. send the command suffixed with an end+exit-code marker
  4. capture everything before the marker, exit with the remote exit code

Usage:
  python3 scripts/pod_exec.py 'nvidia-smi'
  python3 scripts/pod_exec.py --timeout 120 'df -h /workspace'

Reads the ssh target from /tmp/runpod.txt (single line: `ssh <user>-<pod>@ssh.runpod.io -i <key>`).
"""
from __future__ import annotations
import argparse, sys, uuid, base64, hashlib, re
from pathlib import Path
import pexpect

POD_FILE = "/tmp/runpod.txt"
PROMPT_RE = r"root@[0-9a-f]+:[^\r\n]*#"


def read_target() -> list[str]:
    line = open(POD_FILE).read().strip().splitlines()[0].strip()
    return line.removeprefix("ssh ").strip().split()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?")
    ap.add_argument("--upload", type=Path)
    ap.add_argument("--destination")
    ap.add_argument("--timeout", type=int, default=60)
    a = ap.parse_args()
    if a.upload and (not a.destination or not re.fullmatch(r'/root/[a-zA-Z0-9_./-]+', a.destination)):
        ap.error('Upload requires a simple /root destination')
    if not a.upload and not a.cmd:
        ap.error('Need a command or --upload')
    target = read_target()

    child = pexpect.spawn("ssh", ["-tt", "-o", "ConnectTimeout=15", *target],
                          encoding="utf-8", codec_errors="replace", timeout=a.timeout)
    try:
        child.expect(PROMPT_RE, timeout=40)
        # neutralize echo + bracketed paste so long command lines execute
        ready = f"RDY{uuid.uuid4().hex[:6]}"
        child.sendline(f"set +H; stty -echo; bind 'set enable-bracketed-paste off' 2>/dev/null; echo {ready}")
        child.expect(ready, timeout=20)
        child.expect(PROMPT_RE, timeout=20)

        if a.upload:
            data = a.upload.read_bytes()
            encoded = base64.b64encode(data).decode()
            path = a.destination
            def checked(command):
                marker = 'UP' + uuid.uuid4().hex[:10]
                child.sendline(command + '; echo ' + marker + '_$?')
                child.expect(marker + r'_(\d+)', timeout=a.timeout)
                if int(child.match.group(1)):
                    raise RuntimeError('Remote upload command failed')
                child.expect(PROMPT_RE, timeout=20)
            checked(f'umask 077; truncate -s 0 {path}.b64')
            for pos in range(0, len(encoded), 2800):
                checked(f'echo {encoded[pos:pos+2800]} >> {path}.b64')
            digest = hashlib.sha256(data).hexdigest()
            checked(f"base64 -d {path}.b64 > {path}.incoming && chmod 600 {path}.incoming && printf '%s  %s\\n' {digest} {path}.incoming | sha256sum -c --status && mv {path}.incoming {path} && rm {path}.b64")
            print('Upload verified')
            return 0

        end = f"END{uuid.uuid4().hex[:6]}"
        cmd = a.cmd.replace("\\", "\\\\").replace("'", "'\\''")
        child.sendline(f"{cmd}; echo {end}_$?")
        child.expect(end + r"_(\d+)", timeout=a.timeout)
        rc = int(child.match.group(1))
        out = child.before or ""
        try:
            child.expect(PROMPT_RE, timeout=10)
        except pexpect.TIMEOUT:
            pass
        # drop the echoed command's first line if the terminal still echoed it
        lines = [ln for ln in out.replace("\r\n", "\n").replace("\r", "").splitlines()]
        while lines and (cmd[:30] in lines[0] or lines[0].strip() == ""):
            lines = lines[1:]
        print("\n".join(lines))
        return rc
    except pexpect.TIMEOUT:
        print(f"[pod_exec] TIMEOUT after {a.timeout}s — partial output:", file=sys.stderr)
        if not a.upload:
            print(child.before or "", file=sys.stderr)
        return 124
    except pexpect.EOF:
        print('[pod_exec] SSH connection ended unexpectedly', file=sys.stderr)
        return 125
    finally:
        try:
            child.sendline("exit")
            child.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
