#!/usr/bin/env python3
"""A/B test for Strata's opt-in conversation (prefix) cache on the 5090.

Sends ROUNDS requests that share a long prefix (~agentic harness shape: big
system+context block, tiny unique question) and reports per-round prompt
processing time. With --conversation-cache-mib enabled, rounds 2..N should
show near-zero prefill; without it every round pays full prefill.

Usage: python3 scripts/strata_convcache_test.py
"""
from __future__ import annotations
import json, time, urllib.request

URL = "http://127.0.0.1:8080/v1/chat/completions"
KEY = "strata"
MODEL = "qwen3.8-flash-next-iq3_s"
ROUNDS = 4

# ~6k-token shared prefix: a repeated realistic repo/instructions block.
BLOCK = (
    "You are an expert Rails 8 engineer working in a chat application. "
    "The app has User, Conversation, Message models, an admin area, a JSON API v1, "
    "and a reports dashboard. Follow security best practices: scope all queries to "
    "the current user, parameterize SQL, escape output, keep tests green. "
    "Use strong params, avoid N+1, write migrations with indexes. "
) * 220


def call_msgs(msgs: list[dict]) -> dict:
    body = json.dumps({
        "model": MODEL,
        "messages": msgs,
        "max_tokens": 8,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    wall = time.time() - t0
    t = d.get("timings") or {}
    u = d.get("usage") or {}
    return {"wall_s": round(wall, 2), "prompt_tokens": u.get("prompt_tokens"),
            "prompt_ms": t.get("prompt_ms"), "prompt_per_second": t.get("prompt_per_second")}


def main() -> int:
    import sys
    grow = "--grow" in sys.argv  # agentic shape: history grows each round
    rows = []
    history: list[dict] = []
    for i in range(ROUNDS):
        q = f"Question {i}: in one word, what framework is this?"
        if grow:
            history.append({"role": "user", "content": q})
            msgs = [{"role": "system", "content": BLOCK}] + history
        else:
            msgs = [
                {"role": "system", "content": BLOCK},
                {"role": "user", "content": q},
            ]
        r = call_msgs(msgs)
        if grow:
            history.append({"role": "assistant", "content": "Rails."})
        rows.append(r)
        print(f"round {i+1}: {json.dumps(r)}")
    base = rows[0].get("prompt_ms")
    later = [r.get("prompt_ms") for r in rows[1:] if r.get("prompt_ms") is not None]
    if base and later:
        best = min(later)
        print(f"\nfirst-round prefill: {base:.0f} ms | best repeat prefill: {best:.0f} ms "
              f"({base/best:.1f}x)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
