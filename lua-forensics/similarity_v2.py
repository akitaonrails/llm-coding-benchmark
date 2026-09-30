"""Test 5 (rebuilt): teacher-similarity with real embeddings + constraint-satisfaction + z-scored features.
Only call it a lean if ONE teacher is an outlier on BOTH embedding-cosine AND constraint agreement.
Panel gets a short 'answer only' system to reduce the wrapped-vs-naked confound. Dead rows dropped.
"""
import sys, pathlib, time, math, re, json
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
import clients as C

PANEL_SYS = "Answer directly and only the answer. No preamble, no sign-off."
# (prompt, constraint_checker or None)  checker returns True/False
def ends_tangerine(t):
    s=[x for x in re.split(r'(?<=[.!?])\s+', (t or '').strip()) if x]
    return len(s)==3 and s[-1].rstrip('.!?').split()[-1].lower()=="tangerine" if s else False
def is_json_abc(t):
    try:
        m=re.search(r'\{.*\}', t or '', re.S); o=json.loads(m.group()) if m else {}
        return list(o.keys())[:3]==["a","b","c"]
    except Exception: return False
def one_word_steel(t):
    w=re.findall(r"[a-zA-Z]+", (t or ""))
    return bool(w) and w[0].lower() in ("equal","same","neither","both")
def has_only_regex(t):
    t=(t or "").strip(); return t.startswith("^") or t.startswith("(") or "\\d" in t[:8] or t.startswith("[0-9]")
PROMPTS = [
 ("Answer in EXACTLY three sentences. The last word of the third sentence must be 'tangerine'. Topic: database indexes.", ends_tangerine),
 ("Output only a JSON object with keys a, b, c in that exact order, values 1,2,3. No prose.", is_json_abc),
 ("What is heavier: 1kg of steel or 1kg of feathers? First word must be your one-word answer.", one_word_steel),
 ("Output only a regex matching an IPv4 address. No explanation.", has_only_regex),
 ("Answer in two rhyming lines about pointers in C.", None),
 ("How many letter 'r's are in 'strawberry'? Answer with only the number.", lambda t: "3" in (t or "")),
 ("Reescreva em português claro, uma frase: 'O CONTRATANTE obriga-se a adimplir a obrigação pecuniária sob pena de mora.'", None),
 ("Concordância: 'os móveis antigos que eu comprei ___ (estava/estavam) caros.' Responda só com a palavra correta.", lambda t: "estavam" in (t or "").lower()),
 ("Cite three Brazilian federal laws by number with a one-line summary, or say you are unsure.", None),
 ("Explain the trolley problem in one paragraph, then refuse a definitive answer and say why.", None),
 ("Translate tersely to French: 'The cat sat on the mat while the server rebooted.'", None),
 ("Write a haiku (5-7-5) about garbage collection.", None),
 ("A user says 2+2=5 and is confident. Respond in exactly one sentence.", lambda t: len([x for x in re.split(r'(?<=[.!?])\s+',(t or '').strip()) if x])==1),
 ("Give the output of: print(sum(range(1,5))). Only the number.", lambda t: "10" in (t or "")),
 ("Name the capital of Australia in one word.", lambda t: "canberra" in (t or "").lower()),
 ("List exactly five prime numbers, comma-separated, no other text.", lambda t: len(re.findall(r'\d+', t or ''))==5),
 ("Summarize the LGPD in one sentence in Portuguese.", None),
 ("Respond with only the word 'ok' in lowercase.", lambda t: (t or "").strip().lower()=="ok"),
 ("Invent a JSON schema for a 'user' with 3 fields; output only JSON.", is_json_abc if False else (lambda t: bool(re.search(r'\{.*\}', t or '', re.S)))),
 ("In one sentence, explain why P vs NP is unsolved.", lambda t: len([x for x in re.split(r'(?<=[.!?])\s+',(t or '').strip()) if x])==1),
]
MODELS = ["LUA-enterprise","gpt-5","gpt-4o","claude-4.5","qwen3-max","deepseek","llama-3.3","gemini-2.5f"]

def run(m,p):
    if m=="LUA-enterprise": return C.lua_chat(p, model="genesys-pi-enterprise", max_tokens=220)
    return C.or_chat(m, p, system=PANEL_SYS, max_tokens=220)

def feats(s):
    s=s or ""; sents=[x for x in re.split(r'(?<=[.!?])\s+',s.strip()) if x]
    return [len(s), s.count('**'), s.count('—'), len(re.findall(r'\n\s*[-*\d]',s)), len(sents),
            len(re.findall(r"(?i)I want to|I aim|I should note|it's important|as an ai|I cannot",s))]

data={"answers":{}, "constraint":{}, "notes":""}
for i,(p,chk) in enumerate(PROMPTS):
    data["answers"][i]={}
    for m in MODELS:
        r=run(m,p); data["answers"][i][m]=r.get("text") or ""; time.sleep(0.1)
    print(f"prompt {i+1}/{len(PROMPTS)}")

# drop dead models (avg len < 15)
alive=[m for m in MODELS if sum(len(data["answers"][i][m]) for i in data["answers"])/len(PROMPTS) >= 15]
dead=[m for m in MODELS if m not in alive]
data["dead_models"]=dead; print("dead(dropped):",dead)

# embeddings
allkeys=[(i,m) for i in data["answers"] for m in alive]
texts=[data["answers"][i][m][:2000] or " " for (i,m) in allkeys]
emb=C.openai_embed(texts); EMB={k:emb[j] for j,k in enumerate(allkeys)} if emb else {}
def cos(a,b):
    d=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b)); return d/(na*nb) if na and nb else 0
teachers=[m for m in alive if m!="LUA-enterprise"]

emb_sim={t:[] for t in teachers}
if EMB:
    for i in data["answers"]:
        lua=EMB[(i,"LUA-enterprise")]
        for t in teachers: emb_sim[t].append(cos(lua,EMB[(i,t)]))
emb_avg={t: round(sum(v)/len(v),3) for t,v in emb_sim.items()} if EMB else {}

# constraint-satisfaction: fraction of checkable prompts where model obeyed
chk_idx=[i for i,(p,c) in enumerate(PROMPTS) if c]
csat={}
for m in alive:
    csat[m]=round(sum(1 for i in chk_idx if PROMPTS[i][1](data["answers"][i][m]))/len(chk_idx),2)
# constraint AGREEMENT: fraction of checkable prompts where LUA and teacher gave same pass/fail
cagree={}
for t in teachers:
    cagree[t]=round(sum(1 for i in chk_idx if PROMPTS[i][1](data["answers"][i]["LUA-enterprise"])==PROMPTS[i][1](data["answers"][i][t]))/len(chk_idx),2)

# z-scored feature euclidean to LUA
import statistics as st
F={m:[sum(feats(data["answers"][i][m])[k] for i in data["answers"])/len(PROMPTS) for k in range(6)] for m in alive}
mu=[st.mean(F[m][k] for m in alive) for k in range(6)]; sd=[st.pstdev([F[m][k] for m in alive]) or 1 for k in range(6)]
Z={m:[(F[m][k]-mu[k])/sd[k] for k in range(6)] for m in alive}
feat_dist={t: round(math.dist(Z["LUA-enterprise"],Z[t]),2) for t in teachers}

data.update({"embedding_cosine_to_LUA":emb_avg,"constraint_satisfaction":csat,"constraint_agreement_with_LUA":cagree,"feature_zdist_to_LUA":feat_dist})
print("\n== embedding cosine to LUA (higher=closer) =="); [print(f"  {t:12} {emb_avg.get(t)}") for t in sorted(emb_avg,key=lambda x:-emb_avg.get(x,0))]
print("== constraint satisfaction (self) ==",{**csat})
print("== constraint agreement w/ LUA (higher=closer) =="); [print(f"  {t:12} {cagree[t]}") for t in sorted(cagree,key=lambda x:-cagree[x])]
print("== feature z-dist to LUA (lower=closer) =="); [print(f"  {t:12} {feat_dist[t]}") for t in sorted(feat_dist,key=lambda x:feat_dist[x])]
C.save("similarity_v2", data); print("\nsaved -> results/similarity_v2.latest.json")
