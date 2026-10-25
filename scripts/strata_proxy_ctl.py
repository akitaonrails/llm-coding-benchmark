#!/usr/bin/env python3
"""Control the qwen-strata-ondemand proxy: start (detached), stop, status.

The proxy must survive tool-session teardown, so it is spawned with
start_new_session=True (its own session/process group). All process matching
lives here — never put the pattern in a caller's command line (pkill -f
self-match has bitten us 3x today).

Usage: python3 scripts/strata_proxy_ctl.py {start|stop|kill|status|restart|park}
"""
from __future__ import annotations
import os, signal, subprocess, sys, time
from pathlib import Path

PROXY = os.path.expanduser("~/.local/bin/qwen-strata-ondemand")
LOG = "/mnt/data/strata-models/proxy.log"   # NEVER /tmp — tmpfs hit EDQUOT once and silently killed the proxy
ENV = {
    "QWEN_STRATA_CFG": os.path.expanduser("~/.local/state/strata/launch/iq3_s-uncensored-vector.json"),
    "QWEN_IDLE_TTL": "600",
    "QWEN_VRAM_RESERVE_MIB": "4096",  # 2026-10-22: raised 2560->4096; validated holding >=3.6GB free at 99% GPU load
    "QWEN_UP_PORT": "8781",
    "QWEN_PROXY_PORT": "8080",
}
STRATA_LAUNCH_DIR = Path(os.path.expanduser("~/.local/state/strata/launch"))


def _argv(pid: int) -> list[str]:
    try:
        return [part.decode(errors="replace") for part in
                Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0") if part]
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return []


def _matches_proxy(argv: list[str]) -> bool:
    return PROXY in argv


def _matches_engine(argv: list[str]) -> bool:
    if len(argv) < 2 or not argv[1].endswith("/strata.py") or "serve" not in argv:
        return False
    try:
        config = Path(argv[argv.index("--config") + 1])
        return (argv[argv.index("--host") + 1] == "127.0.0.1"
                and argv[argv.index("--port") + 1] == ENV["QWEN_UP_PORT"]
                and config.parent == STRATA_LAUNCH_DIR
                and config.name.startswith("iq3_s"))
    except (ValueError, IndexError):
        return False


def _matching_pids(predicate) -> list[int]:
    matches = []
    for proc in Path("/proc").iterdir():
        if proc.name.isdigit():
            pid = int(proc.name)
            if pid != os.getpid() and predicate(_argv(pid)):
                matches.append(pid)
    return matches


def pids() -> list[int]:
    return _matching_pids(_matches_proxy)


def engine_pids() -> list[int]:
    return _matching_pids(_matches_engine)


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
    """Immediately kill this proxy and its matching Strata engine."""
    for _ in range(20):
        # Rescan so an engine spawned during a concurrent cold start is killed too.
        for predicate, owned_pids in ((_matches_proxy, pids()),
                                      (_matches_engine, engine_pids())):
            for pid in owned_pids:
                if not predicate(_argv(pid)):
                    continue
                try:
                    if os.getpgid(pid) == pid and os.getsid(pid) == pid:
                        os.killpg(pid, signal.SIGKILL)
                    else:
                        os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        if not pids() and not engine_pids() and not port_up():
            print("stopped")
            return 0
        time.sleep(0.1)
    print(f"STILL_RUNNING proxy={pids()} engine={engine_pids()}")
    return 1


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
    if cmd in ("stop", "kill"):
        return stop()
    if cmd == "restart":
        if stop():
            return 1
        return start()
    if cmd == "park":
        return park()
    print("up" if port_up() else "down", f"pids={pids()}")
    return 0 if port_up() else 1


if __name__ == "__main__":
    sys.exit(main())
