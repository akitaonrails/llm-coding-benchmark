"""Test 2 (rebuilt): glitch-token panel with controls, repetition, house/enterprise split.
Glitch-rate on o200k-junk vs well-trained controls separates:
  - fails glitch, copies controls  -> o200k-native undertrained embeddings (own or inherited)
  - same SUBSTITUTION STRING as gpt-4o -> embedding-lineage lean
  - same failure CLASS, different garbage -> borrowed vocab, own table
  - fails controls too -> just weak at CJK (no conclusion)
"""
import sys, pathlib, time, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
import clients as C

norm = lambda s: unicodedata.normalize("NFC", s)
GLITCH = [norm(x) for x in ["植物百科通","给主人留下些什么吧","微信公众号","龙腾世纪","彩神争霸","请稍候片刻","bagbogbo","Japgolly"]]
CONTROL = [norm(x) for x in ["中国","谢谢","你好","世界","强大","strawberry","provavelmente"]]
PROMPT = "Repeat this exact string between <r> and </r>, nothing else: "
LUA = {"LUA-house":"genesys-pi-house","LUA-enterprise":"genesys-pi-enterprise"}
PANEL = ["gpt-4o","gpt-4o-mini","gpt-oss-120b","gpt-oss-20b","gpt-5","claude-4.5","qwen3-max"]
N_LUA, N_PANEL = 3, 1

def call(model_label, s):
    # LUA is fast/non-reasoning at 40; panel gets a big budget so reasoning
    # models (gpt-5, gpt-oss) don't spend the whole allowance on hidden reasoning
    # and return empty (the "dead" rows in the first run).
    if model_label in LUA: return C.lua_chat(PROMPT+s, model=LUA[model_label], max_tokens=40)
    return C.or_chat(model_label, PROMPT+s, max_tokens=256)

def reproduced(text, s): return s in (text or "")

def run_set(model_label, strings, n):
    res = {}
    for s in strings:
        outs = []
        for _ in range(n):
            r = call(model_label, s); outs.append(r.get("text") or (f"[ERR]" if r.get("error") else ""))
            time.sleep(0.15)
        ok = sum(reproduced(o, s) for o in outs)
        res[s] = {"reproduced": ok, "n": n, "rate_fail": round(1 - ok/n, 2), "samples": outs}
    return res

data = {"glitch_set": GLITCH, "control_set": CONTROL, "by_model": {}}
models = [(m, N_LUA) for m in LUA] + [(m, N_PANEL) for m in PANEL]
for m, n in models:
    g = run_set(m, GLITCH, n); c = run_set(m, CONTROL, n)
    gfail = round(sum(v["rate_fail"] for v in g.values())/len(g), 2)
    cfail = round(sum(v["rate_fail"] for v in c.values())/len(c), 2)
    data["by_model"][m] = {"glitch_fail_rate": gfail, "control_fail_rate": cfail, "glitch": g, "control": c}
    print(f"{m:16} glitch_fail={gfail}  control_fail={cfail}")

# substitution-string comparison vs gpt-4o on the shared glitch strings (embedding-lineage tell)
print("\n== per-glitch first-sample outputs (LUA-E vs gpt-4o vs gpt-oss) ==")
for s in GLITCH:
    le = data["by_model"]["LUA-enterprise"]["glitch"][s]["samples"][0].replace("\n"," ")[:40]
    g4 = data["by_model"]["gpt-4o"]["glitch"][s]["samples"][0].replace("\n"," ")[:40]
    go = data["by_model"]["gpt-oss-120b"]["glitch"][s]["samples"][0].replace("\n"," ")[:40]
    same_as_gpt4o = (le == g4 and not reproduced(le, s))
    print(f"  {s:12} LUA-E={le!r:44} gpt4o={g4!r:30} {'<= SAME AS GPT4O' if same_as_gpt4o else ''}")

C.save("glitch_panel", data)
print("\nsaved -> results/glitch_panel.latest.json")
