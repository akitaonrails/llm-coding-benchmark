#!/usr/bin/env python3
"""Control the qwen-strata-ondemand proxy: start (detached), stop, status.

The proxy must survive tool-session teardown, so it is spawned with
start_new_session=True (its own session/process group). All process matching
lives here — never put the pattern in a caller's command line (pkill -f
self-match has bitten us 3x today).

Usage: python3 scripts/strata_proxy_ctl.py {start|stop|status|restart}
"""
from __future__ import annotations
import os, signal, subprocess, sys, time
from pathlib import Path

PROXY = os.path.expanduser("~/.local/bin/qwen-strata-ondemand")
LOG = "/mnt/data/strata-models/proxy.log"   # NEVER /tmp — tmpfs hit EDQUOT once and silently killed the proxy
ENV = {
    "QWEN_IDLE_TTL": "600",
    "QWEN_VRAM_RESERVE_MIB": "4096",  # 2026-10-22: raised 2560->4096; validated holding >=3.6GB free at 99% GPU load
    "QWEN_UP_PORT": "8781",
    "QWEN_PROXY_PORT": "8080",
}
PAT = "qwen-strata-ondemand"


def pids() -> list[int]:
    out = subprocess.run(["pgrep", "-f", PAT], capture_output=True, text=True).stdout
    me = os.getpid()
    return [int(p) for p in out.split() if int(p) != me]


def port_up() -> bool:
    out = subprocess.run(["ss", "-ltn"], capture_output=True, text=True).stdout
    return ":8080 " in out or ":8080\n" in out


def start() -> int:
    if port_up():
        print(f"already up (pids={pids()})")
        return 0
    env = {**os.environ, **ENV}
    with open(LOG, "ab", 0) as f:
        subprocess.Popen([PROXY], stdin=subprocess.DEVNULL, stdout=f, stderr=f,
                         env=env, start_new_session=True)
    for _ in range(20):
        time.sleep(0.5)
        if port_up():
            print(f"PROXY_UP pids={pids()}")
            return 0
    print("PROXY_FAILED — log tail:")
    os.system(f"tail -5 {LOG}")
    return 1


def stop() -> int:
    ps = pids()
    for p in ps:
        try:
            os.kill(p, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(2)
    for p in pids():
        try:
            os.kill(p, signal.SIGKILL)
        except ProcessLookupError:
            pass
    print("stopped" if not pids() else "STILL_RUNNING")
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        return start()
    if cmd == "stop":
        return stop()
    if cmd == "restart":
        stop()
        return start()
    print("up" if port_up() else "down", f"pids={pids()}")
    return 0 if port_up() else 1


if __name__ == "__main__":
    sys.exit(main())
