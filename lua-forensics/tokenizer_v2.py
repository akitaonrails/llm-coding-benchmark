"""Test 1 (rebuilt) + Test 6: tokenizer counts with explicit o200k_base vs o200k_harmony,
house+enterprise as separate artifacts, and PT-vs-EN fertility (marketing check).
Delta: content_tokens(S) = pt(S+S) - pt(S). Strings pinned utf-8, single trailing NL stripped, repr logged.
"""
import sys, pathlib, time, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
import clients as C
import tiktoken
from transformers import AutoTokenizer

o200k = tiktoken.get_encoding("o200k_base")
harmony = tiktoken.get_encoding("o200k_harmony")
cl100k = tiktoken.get_encoding("cl100k_base")
hf = {"Qwen3":"Qwen/Qwen3-8B","DeepSeek":"deepseek-ai/DeepSeek-V2-Lite","Llama3":"NousResearch/Meta-Llama-3-8B",
      "Mistral":"mistral-community/Mistral-7B-v0.2","BERTimbau":"neuralmind/bert-base-portuguese-cased","Tucano":"TucanoBR/Tucano-2b4"}
def txtlen(enc): return lambda s: len(enc.encode(s, disallowed_special=()))
TOK = {"o200k_base": txtlen(o200k), "o200k_harmony_text": txtlen(harmony), "cl100k": txtlen(cl100k)}
for n,r in hf.items():
    t = AutoTokenizer.from_pretrained(r, trust_remote_code=True); TOK[n] = (lambda s,t=t: len(t.encode(s, add_special_tokens=False)))

def norm(s): return unicodedata.normalize("NFC", s).rstrip("\n")
TEXTS = {k: norm(v) for k,v in {
 "digits20":"0123456789"*20, "cjk":"人工智能正在迅速改变世界经济和社会结构，深度学习模型的能力持续增强。"*2,
 "pt_accents":"não, coração, informações, opções, inconstitucionalidade, você, saudade, José e a programação."*2,
 "english":"The quick brown fox jumps over the lazy dog and reshapes the global economy."*2,
 "emoji_zwj":"👨‍👩‍👧‍👦🇧🇷👩🏽‍💻🧑‍🚀 "*6,
}.items()}

def lua_ct(s, model):
    a=C.lua_prompt_tokens(s,model=model); time.sleep(0.1); b=C.lua_prompt_tokens(s+s,model=model); time.sleep(0.1)
    return (b-a) if (a is not None and b is not None) else None

out={"text_table":{}, "harmony_specials":{}, "fertility":{}, "distance":{}}
print("== TEXT COUNTS (X+X - X); LUA house & enterprise separate ==")
print("  ".join(f"{h:>10}" for h in ["string"]+list(TOK)+["LUA-H","LUA-E"]))
lv={}
for name,s in TEXTS.items():
    refs={k:fn(s) for k,fn in TOK.items()}
    h=lua_ct(s,"genesys-pi-house"); e=lua_ct(s,"genesys-pi-enterprise"); lv[name]=(h,e)
    out["text_table"][name]={"repr":repr(s)[:60],**refs,"LUA_house":h,"LUA_enterprise":e}
    print("  ".join([f"{name:>10}"]+[f"{refs[k]:>10}" for k in TOK]+[f"{str(h):>10}",f"{str(e):>10}"]))

for k,fn in TOK.items():
    out["distance"][k]=sum(abs(fn(TEXTS[t])-lv[t][1]) for t in TEXTS if lv[t][1] is not None)
print("\n== distance to LUA-enterprise (lower=closer) ==");
for k in sorted(out["distance"],key=lambda x:out["distance"][x]): print(f"  {k:>18}: {out['distance'][k]}")

print("\n== HARMONY special tokens: o200k_base(text) vs o200k_harmony(native) vs LUA ==")
HSPEC=["<|start|>","<|channel|>","<|message|>","<|call|>","<|end|>"]
print(f"{'token':>14}{'base_txt':>10}{'harmony':>9}{'LUA-E':>7}")
for t in HSPEC:
    bt=len(o200k.encode(t,disallowed_special=())); hn=len(harmony.encode(t,allowed_special='all')); le=lua_ct(t,"genesys-pi-enterprise")
    out["harmony_specials"][t]={"o200k_base_text":bt,"o200k_harmony_native":hn,"LUA_enterprise":le}
    print(f"{t:>14}{bt:>10}{hn:>9}{str(le):>7}")
# harmony substrings inside a normal English sentence (should be pure text everywhere)
sent=norm("Please use the channel to start the message and end the call properly.")
out["harmony_specials"]["_english_sentence"]={"repr":repr(sent),"o200k_base":len(o200k.encode(sent)),"LUA_E":lua_ct(sent,"genesys-pi-enterprise")}

print("\n== FERTILITY: tokens per char, PT vs EN (marketing check) ==")
PT=norm("A soberania de dados exige que o processamento de informações permaneça no país, com governança própria e verificação independente das afirmações do fornecedor sobre a origem do modelo.")
EN=norm("Data sovereignty requires that information processing remain in-country, with proper governance and independent verification of the vendor's claims about the model's origin.")
print(f"{'tokenizer':>18}{'PT/char':>9}{'EN/char':>9}{'PT/EN':>7}")
for label,enc in [("o200k_base",txtlen(o200k)),("BERTimbau",TOK["BERTimbau"]),("Tucano",TOK["Tucano"])]:
    pt=enc(PT); en=enc(EN); out["fertility"][label]={"PT":pt,"EN":en,"PT_per_char":round(pt/len(PT),3),"EN_per_char":round(en/len(EN),3)}
    print(f"{label:>18}{pt/len(PT):>9.3f}{en/len(EN):>9.3f}{pt/en:>7.2f}")
lpt=lua_ct(PT,"genesys-pi-enterprise"); len_pt=lua_ct(EN,"genesys-pi-enterprise")
out["fertility"]["LUA_enterprise"]={"PT":lpt,"EN":len_pt,"PT_per_char":round(lpt/len(PT),3) if lpt else None,"EN_per_char":round(len_pt/len(EN),3) if len_pt else None}
print(f"{'LUA_enterprise':>18}{(lpt/len(PT)) if lpt else 0:>9.3f}{(len_pt/len(EN)) if len_pt else 0:>9.3f}{(lpt/len_pt) if (lpt and len_pt) else 0:>7.2f}")
C.save("tokenizer_v2", out); print("\nsaved -> results/tokenizer_v2.latest.json")
