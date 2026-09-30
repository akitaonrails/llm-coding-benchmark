"""Test 5: parallel teacher-similarity grid (the distillation lean).
Run idiosyncratic prompts on LUA + a reference panel; measure how close LUA's answers
are to each teacher (char n-gram cosine + structural features). Distill-from-X shows up
as LUA systematically closest to X on odd-constraint prompts. NOT proof — a lean.
"""
import sys, pathlib, time, math, re
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
import clients as C

PROMPTS = [
 "Answer with exactly three sentences. The last word of the third sentence must be 'tangerine'. Topic: why indices speed up databases.",
 "In one paragraph, no lists, explain the trolley problem and then refuse to give a definitive answer, explaining why you refuse.",
 "Write a regex that matches an IPv4 address with no capturing groups. Output only the regex, nothing else.",
 "Reescreva esta cláusula em português claro: 'O CONTRATANTE obriga-se a adimplir a obrigação pecuniária no prazo avençado, sob pena de mora.'",
 "Plan (do not execute) how you would grep a Rails repo to find where the RubyLLM gem is configured. List the exact shell commands.",
 "What is heavier: one kilogram of steel or one kilogram of feathers? Answer in one word, then explain in one sentence.",
 "You have 3 sentences to convince a skeptic that P != NP is unproven. Go.",
 "Give me a JSON object (only JSON) describing a book: title, author, year, genres (array of 2).",
 "Complete this exactly and only this: 'The mitochondria is the ___ of the cell.'",
 "Name three Brazilian federal laws by number and one-line summary each. Be precise or say you are unsure.",
 "Translate to French, keep it terse: 'The cat sat on the mat while the server rebooted.'",
 "Write a haiku about garbage collection in programming. 5-7-5.",
]
MODELS = ["LUA-enterprise", "gpt-oss-120b", "gpt-5", "gpt-4o", "claude-4.5", "qwen3-max", "deepseek", "llama-3.3", "gemini-2.5f"]

def run(label, p):
    if label == "LUA-enterprise": return C.lua_chat(p, model="genesys-pi-enterprise", max_tokens=300)
    return C.or_chat(label, p, max_tokens=300)

def ngrams(s, n=4):
    s = re.sub(r"\s+", " ", (s or "").strip().lower())
    return Counter(s[i:i+n] for i in range(max(0, len(s)-n+1)))

def cosine(a, b):
    ks = set(a) | set(b)
    dot = sum(a[k]*b[k] for k in ks); na = math.sqrt(sum(v*v for v in a.values())); nb = math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb) if na and nb else 0.0

def feats(s):
    s = s or ""
    return {"len": len(s), "bullets": s.count("\n- ")+s.count("\n* ")+len(re.findall(r"\n\d+\.", s)),
            "emdash": s.count("—"), "bold": s.count("**"), "hedge": len(re.findall(r"(?i)I want to be|I aim to|I should note|it's important to|I'm not able|as an ai", s))}

data = {"prompts": PROMPTS, "answers": {}, "features": {}}
for p_i, p in enumerate(PROMPTS):
    data["answers"][p_i] = {}
    for m in MODELS:
        r = run(m, p); data["answers"][p_i][m] = r.get("text") or (f"[ERR {r.get('error')}]" if r.get("error") else "")
        time.sleep(0.15)
    print(f"prompt {p_i+1}/{len(PROMPTS)} done")

# pairwise similarity LUA vs each teacher (avg cosine over prompts)
teachers = [m for m in MODELS if m != "LUA-enterprise"]
sim = {t: [] for t in teachers}
for p_i in data["answers"]:
    lua = ngrams(data["answers"][p_i]["LUA-enterprise"])
    for t in teachers:
        sim[t].append(cosine(lua, ngrams(data["answers"][p_i][t])))
avg = {t: sum(v)/len(v) for t, v in sim.items()}
data["avg_cosine_to_LUA"] = avg
# structural feature averages
for m in MODELS:
    fs = [feats(data["answers"][p_i][m]) for p_i in data["answers"]]
    data["features"][m] = {k: round(sum(f[k] for f in fs)/len(fs), 2) for k in fs[0]}

print("\n== avg char-4gram cosine of each teacher to LUA (higher = more similar) ==")
for t in sorted(avg, key=lambda x: -avg[x]):
    print(f"  {t:14} {avg[t]:.3f}")
print("\n== structural features (avg) ==")
print(f"{'model':16}{'len':>6}{'bullets':>8}{'emdash':>7}{'bold':>6}{'hedge':>6}")
for m in MODELS:
    f = data["features"][m]; print(f"{m:16}{f['len']:>6}{f['bullets']:>8}{f['emdash']:>7}{f['bold']:>6}{f['hedge']:>6}")
C.save("similarity_grid", data)
print("\nsaved -> lua-forensics/results/similarity_grid.latest.json")
