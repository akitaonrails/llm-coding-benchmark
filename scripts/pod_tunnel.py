#!/usr/bin/env python3
"""Hold a persistent SSH tunnel to the RunPod pod: localhost:8100 -> pod:8000.

RunPod's SSH proxy ignores remote commands and requires a PTY, so plain
`ssh -N -L` is refused. This daemon opens the interactive session with -tt and
a local forward, waits for the shell prompt, then sleeps — the forward stays
live as long as the session does. If the session dies, this process exits
nonzero (supervise with a loop or systemd-run if needed).

Usage: nohup python3 scripts/pod_tunnel.py > /tmp/opencode/b300/tunnel.log 2>&1 &
"""
from __future__ import annotations
import sys, time
import pexpect

POD_FILE = "/tmp/runpod.txt"
PROMPT_RE = r"root@[0-9a-f]+:[^\r\n]*#"


def main() -> int:
    target = open(POD_FILE).read().strip().splitlines()[0].removeprefix("ssh ").split()
    child = pexpect.spawn(
        "ssh",
        ["-tt", "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30",
         "-o", "ServerAliveCountMax=6", "-o", "ExitOnForwardFailure=yes",
         "-L", "8100:localhost:8000", *target],
        encoding="utf-8", codec_errors="replace", timeout=60)
    child.logfile_read = sys.stdout
    child.expect(PROMPT_RE, timeout=45)   # banner + prompt
    print(f"\n[tunnel] session up, forward localhost:8100 -> pod:8000", flush=True)
    # keep the session alive indefinitely; exit if ssh dies
    while True:
        try:
            idx = child.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=30)
        except Exception:
            break
        if idx == 0:
            print("[tunnel] ssh exited", flush=True)
            return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
