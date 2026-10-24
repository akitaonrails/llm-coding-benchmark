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


def park() -> int:
    """Stop the ENGINE (free all VRAM) but keep the on-demand proxy up.

    Mirrors the wrapper's stop_up() patterns — they live here so callers never
    put them in a harness command line (self-match kills, 2026-10-22).
    """
    import subprocess as sp
    for pat in ("iq3_s-128k.json", "packs/iq3_s ", "Qwen3.8-Flash-Next"):
        sp.run(["pkill", "-TERM", "-f", pat], capture_output=True)
    time.sleep(4)
    for _ in range(20):
        out = sp.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader"],
                     capture_output=True, text=True).stdout.strip()
        used = int(out.split()[0]) if out else 0
        if used < 1500:
            print(f"ENGINE_PARKED vram_used={used}MiB")
            return 0
        time.sleep(2)
    print(f"ENGINE_STILL_LOADED vram_used={out}")
    return 1


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        return start()
    if cmd == "stop":
        return stop()
    if cmd == "restart":
        stop()
        return start()
    if cmd == "park":
        return park()
    print("up" if port_up() else "down", f"pids={pids()}")
    return 0 if port_up() else 1


if __name__ == "__main__":
    sys.exit(main())
