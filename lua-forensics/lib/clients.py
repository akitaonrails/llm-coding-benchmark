"""Shared clients + helpers for LUA Vision provenance forensics.
Stdlib-only networking (urllib). Keys read from ~/.config/zsh/secrets (never printed).
Reference panel via OpenRouter (uniform API for all families).
"""
from __future__ import annotations
import os, json, time, urllib.request, urllib.error, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

def _secret(name):
    p = os.path.expanduser("~/.config/zsh/secrets")
    for line in open(p):
        if line.startswith(f"export {name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(name)

LUA_KEY = _secret("LUA_API_KEY")
OR_KEY = _secret("OPENROUTER_API_KEY")
OPENAI_KEY = _secret("OPENAI_API_KEY")

# Reference panel: label -> OpenRouter model id. gpt-oss-120b is the key gpt-oss tell.
PANEL = {
    "gpt-oss-120b":  "openai/gpt-oss-120b",
    "gpt-oss-20b":   "openai/gpt-oss-20b",
    "gpt-5":         "openai/gpt-5",
    "gpt-4o":        "openai/gpt-4o",
    "gpt-4o-mini":   "openai/gpt-4o-mini",
    "claude-4.5":    "anthropic/claude-sonnet-4.5",
    "qwen3-max":     "qwen/qwen3-max",
    "qwen3-235b":    "qwen/qwen3-235b-a22b",
    "deepseek":      "deepseek/deepseek-chat",
    "llama-3.3":     "meta-llama/llama-3.3-70b-instruct",
    "gemini-2.5f":   "google/gemini-2.5-flash",
}

def _post(url, body, headers, timeout=90, retries=3):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    last = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read()), None
        except urllib.error.HTTPError as e:
            try: last = json.loads(e.read())
            except Exception: last = {"error": {"status": e.code}}
            if e.code in (429, 500, 502, 503): time.sleep(3); continue
            return None, last
        except Exception as e:
            last = {"error": {"exception": str(e)[:120]}}; time.sleep(2)
    return None, last

def lua_chat(user, system=None, model="genesys-pi-enterprise", max_tokens=256):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    d, err = _post("https://api.lua.vision/v1/chat/completions",
                   {"model": model, "messages": msgs, "max_tokens": max_tokens},
                   {"Authorization": f"Bearer {LUA_KEY}", "Content-Type": "application/json"})
    if err: return {"error": err}
    ch = (d.get("choices") or [{}])[0]
    return {"text": (ch.get("message") or {}).get("content"),
            "finish": ch.get("finish_reason"), "usage": d.get("usage")}

def lua_prompt_tokens(user, model="genesys-pi-enterprise"):
    r = lua_chat(user, model=model, max_tokens=1)
    return (r.get("usage") or {}).get("prompt_tokens") if "usage" in r else None

def or_chat(label, user, system=None, max_tokens=256):
    model = PANEL[label]
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    d, err = _post("https://openrouter.ai/api/v1/chat/completions",
                   {"model": model, "messages": msgs, "max_tokens": max_tokens},
                   {"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"})
    if err: return {"error": err}
    ch = (d.get("choices") or [{}])[0]
    return {"text": (ch.get("message") or {}).get("content"), "finish": ch.get("finish_reason")}

def openai_embed(texts, model="text-embedding-3-small"):
    d, err = _post("https://api.openai.com/v1/embeddings",
                   {"model": model, "input": texts},
                   {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"})
    if err: return None
    return [row["embedding"] for row in d["data"]]

def lua_raw_timed(body, model="genesys-pi-enterprise"):
    """POST raw body to LUA; return (status, error_json_or_None, elapsed_s, content_len)."""
    b = dict(body); b["model"] = model
    data = json.dumps(b).encode()
    req = urllib.request.Request("https://api.lua.vision/v1/chat/completions", data=data,
        headers={"Authorization": f"Bearer {LUA_KEY}", "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            j = json.loads(r.read()); dt = time.time() - t0
            txt = ((j.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            return r.status, None, dt, len(txt), (j.get("usage") or {})
    except urllib.error.HTTPError as e:
        dt = time.time() - t0
        try: ej = json.loads(e.read())
        except Exception: ej = {"status": e.code}
        return e.code, ej, dt, 0, {}
    except Exception as e:
        return None, {"exception": str(e)[:120]}, time.time() - t0, 0, {}

def save(name, obj):
    ts = time.strftime("%Y%m%d-%H%M%S")
    p = RESULTS / f"{name}.{ts}.json"
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
    latest = RESULTS / f"{name}.latest.json"
    latest.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
    return p
