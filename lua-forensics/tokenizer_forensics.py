"""Test 1+3: tokenizer family + gpt-oss/Harmony special-token discriminator.
Delta method (Grok): content_tokens(S) = pt(S+S) - pt(S)  [cancels system prompt + boundary].
Compares LUA to o200k_base/harmony, cl100k, Qwen2.5/3, DeepSeek, Llama3, Mistral.
Special tokens: if a family sentinel encodes to ~1 token in LUA it's native to LUA's vocab.
"""
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
import clients as C
import tiktoken
from transformers import AutoTokenizer

o200k = tiktoken.get_encoding("o200k_base")
cl100k = tiktoken.get_encoding("cl100k_base")
try:
    harmony = tiktoken.get_encoding("o200k_harmony"); HARMONY_OK = True
except Exception:
    harmony = None; HARMONY_OK = False
hf = {"Qwen2.5":"Qwen/Qwen2.5-7B","Qwen3":"Qwen/Qwen3-8B","DeepSeek":"deepseek-ai/DeepSeek-V2-Lite",
      "Llama3":"NousResearch/Meta-Llama-3-8B","Mistral":"mistral-community/Mistral-7B-v0.2"}
TOK = {"o200k_base": (lambda s: len(o200k.encode(s))), "cl100k": (lambda s: len(cl100k.encode(s)))}
for n, r in hf.items():
    t = AutoTokenizer.from_pretrained(r, trust_remote_code=True)
    TOK[n] = (lambda s, t=t: len(t.encode(s, add_special_tokens=False)))

TEXTS = {
 "digits20":   "0123456789" * 20,
 "cjk":        "人工智能正在迅速改变世界经济和社会结构，深度学习模型的能力持续增强。" * 2,
 "pt_accents": "não, coração, informações, opções, inconstitucionalidade, você, saudade, José e a programação." * 2,
 "english":    "The quick brown fox jumps over the lazy dog and reshapes the global economy." * 2,
 "emoji_zwj":  "👨‍👩‍👧‍👦🇧🇷👩🏽‍💻🧑‍🚀 " * 6,
 "base64":     "aGVsbG8gd29ybGQgdGhpcyBpcyBhIHRlc3Qgb2YgYmFzZTY0IGVuY29kaW5n" * 2,
 "regex":      r"^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+)@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$" * 2,
}
# family sentinels: label -> (string, which family it's native to)
SPECIALS = {
 "chatml_im_start": "<|im_start|>",         # GPT/Qwen ChatML
 "endoftext":       "<|endoftext|>",        # GPT o200k special
 "harmony_start":   "<|start|>",            # gpt-oss Harmony
 "harmony_channel": "<|channel|>",          # gpt-oss Harmony (KEY gpt-oss tell)
 "harmony_message": "<|message|>",          # gpt-oss Harmony
 "harmony_end":     "<|end|>",              # gpt-oss Harmony
 "llama_bot":       "<|begin_of_text|>",    # Llama3
 "llama_hdr":       "<|start_header_id|>",  # Llama3
 "deepseek_bos":    "<｜begin▁of▁sentence｜>", # DeepSeek
 "gemma_turn":      "<start_of_turn>",      # Gemma
}

def lua_content_tokens(s):
    a = C.lua_prompt_tokens(s); time.sleep(0.15)
    b = C.lua_prompt_tokens(s + s); time.sleep(0.15)
    return (b - a) if (a is not None and b is not None) else None

out = {"harmony_encoding_available": HARMONY_OK, "text_table": {}, "distance": {}, "specials": {}}

print("== TEXT TOKEN COUNTS (delta X+X - X) ==")
hdr = ["string"] + list(TOK) + ["LUA"]
print("  ".join(f"{h:>11}" for h in hdr))
lua_vec = {}
for name, s in TEXTS.items():
    refs = {k: fn(s) for k, fn in TOK.items()}
    lua = lua_content_tokens(s); lua_vec[name] = lua
    out["text_table"][name] = {**refs, "LUA": lua}
    print("  ".join([f"{name:>11}"] + [f"{refs[k]:>11}" for k in TOK] + [f"{lua:>11}" if lua is not None else f"{'ERR':>11}"]))

print("\n== distance to LUA (Σ|ref-LUA|, lower=closer) ==")
for k, fn in TOK.items():
    d = sum(abs(fn(TEXTS[t]) - lua_vec[t]) for t in TEXTS if lua_vec.get(t) is not None)
    out["distance"][k] = d
for k in sorted(out["distance"], key=lambda x: out["distance"][x]):
    print(f"  {k:>11}: {out['distance'][k]}")

print("\n== SPECIAL-TOKEN single-token test (LUA content tokens vs o200k-as-text) ==")
print(f"{'sentinel':>16} {'LUA':>5} {'o200k_txt':>10}  native?")
for name, s in SPECIALS.items():
    try:
        lua = lua_content_tokens(s)
    except Exception as e:
        lua = None
    o_txt = len(o200k.encode(s, disallowed_special=()))
    native = (lua is not None and lua <= 1)
    out["specials"][name] = {"string": s, "LUA": lua, "o200k_text": o_txt, "native_1tok": native}
    tag = "YES(1tok)" if native else ("REJECTED/None" if lua is None else "no(text)")
    print(f"{name:>16} {str(lua):>5} {o_txt:>10}  {tag}")

C.save("tokenizer_forensics", out)
print("\nsaved -> lua-forensics/results/tokenizer_forensics.latest.json")
