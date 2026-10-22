#!/usr/bin/env python3
"""Live VRAM-reserve load test for the Strata engine on the 5090.

Phases:
  A) single long generation (max_tokens=3000) — sustained decode stress
  B) 3 concurrent generations — cache + KV pressure
Samples free VRAM + GPU util every 2s throughout; reports the MINIMUM free VRAM
per phase (the number that decides whether Hyprland survives).

PASS: min free >= 3400 MiB (reserve 4096 minus eviction granularity slack).
Usage: python3 scripts/strata_vram_loadtest.py
"""
from __future__ import annotations
import json, subprocess, threading, time, urllib.request

URL = "http://127.0.0.1:8080/v1/chat/completions"
KEY = "strata"
MODEL = "qwen3.8-flash-next-iq3_s"
PASS_MIN_FREE_MIB = 3400

_samples: list[tuple[str, int, int]] = []
_stop = threading.Event()


def sampler(phase: str) -> None:
    while not _stop.is_set():
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free,utilization.gpu",
                              "--format=csv,noheader,nounits"], capture_output=True,
                             text=True).stdout.strip()
        try:
            free, util = (int(x) for x in out.split(", "))
            _samples.append((phase, free, util))
        except Exception:
            pass
        time.sleep(2)


def gen(max_tokens: int, seed: int, results: list, idx: int) -> None:
    prompts = [
        "Write a detailed 600-word technical essay about lighthouse optics and Fresnel lenses.",
        "Explain the history of maritime navigation, radar, and GPS in 600 words.",
        "Describe the physics of ocean waves, tides, and coastal erosion in 600 words.",
    ]
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompts[seed]}],
                       "max_tokens": max_tokens, "temperature": 0.8}).encode()
    req = urllib.request.Request(URL, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {KEY}"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=1200) as r:
            d = json.load(r)
        tps = (d.get("timings") or {}).get("predicted_per_second")
        results[idx] = {"ok": True, "tok_s": tps, "s": round(time.time() - t0, 1),
                        "completion": d.get("usage", {}).get("completion_tokens")}
    except Exception as e:
        results[idx] = {"ok": False, "error": str(e)[:120], "s": round(time.time() - t0, 1)}


def phase(name: str, workers: list[tuple[int, int]]) -> dict:
    _samples.clear()
    t = threading.Thread(target=sampler, args=(name,), daemon=True)
    t.start()
    results: list = [None] * len(workers)
    threads = [threading.Thread(target=gen, args=(mt, seed, results, i))
               for i, (mt, seed) in enumerate(workers)]
    t0 = time.time()
    for th in threads: th.start()
    for th in threads: th.join()
    time.sleep(3)                     # capture post-generation settle
    _stop.set(); t.join(); _stop.clear()
    frees = [f for (_, f, _) in _samples]
    utils = [u for (_, _, u) in _samples]
    return {"phase": name, "wall_s": round(time.time() - t0, 1),
            "min_free_mib": min(frees), "max_free_mib": max(frees),
            "peak_util_pct": max(utils), "samples": len(frees),
            "requests": results,
            "pass": min(frees) >= PASS_MIN_FREE_MIB}


def main() -> int:
    print("Phase A: single long generation")
    a = phase("A", [(3000, 0)])
    print(json.dumps({k: v for k, v in a.items() if k != "requests"}, indent=1))
    print("Phase B: 3 concurrent generations")
    b = phase("B", [(2000, 0), (2000, 1), (2000, 2)])
    print(json.dumps({k: v for k, v in b.items() if k != "requests"}, indent=1))
    print("requests:", json.dumps(a["requests"] + b["requests"], indent=1))
    ok = a["pass"] and b["pass"] and all(r["ok"] for r in a["requests"] + b["requests"])
    print(f"\nRESULT: {'PASS' if ok else 'FAIL'} — min free A={a['min_free_mib']}MiB "
          f"B={b['min_free_mib']}MiB (floor {PASS_MIN_FREE_MIB}MiB)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
