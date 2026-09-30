"""Test 4 (rebuilt): infra/gateway fingerprint. Latency vs output length, context-limit error text,
extra-param handling (min_p/top_k/repetition_penalty/enable_thinking/reasoning_effort). house vs enterprise.
"""
import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
import clients as C

MODELS = {"house":"genesys-pi-house","enterprise":"genesys-pi-enterprise"}
out = {"latency": {}, "context_limits": {}, "extra_params": {}}

print("== LATENCY: elapsed & tok/s for small vs large output ==")
for lbl, mid in MODELS.items():
    row = {}
    for tag, mt in [("out20", 20), ("out400", 400)]:
        st, err, dt, clen, usage = C.lua_raw_timed(
            {"messages":[{"role":"user","content":"Write about databases."}], "max_tokens": mt}, model=mid)
        ct = (usage or {}).get("completion_tokens")
        row[tag] = {"status": st, "elapsed_s": round(dt,2), "completion_tokens": ct,
                    "tok_per_s": round(ct/dt,1) if (ct and dt) else None}
        time.sleep(0.3)
    out["latency"][lbl] = row
    print(f"  {lbl:10} out20={row['out20']['elapsed_s']}s/{row['out20']['tok_per_s']}tps  "
          f"out400={row['out400']['elapsed_s']}s/{row['out400']['tok_per_s']}tps")

print("\n== CONTEXT LIMITS: error wording at escalating sizes (enterprise, 384K ctx) ==")
for chars in [50_000, 200_000, 500_000, 1_000_000, 2_000_000]:
    st, err, dt, clen, usage = C.lua_raw_timed(
        {"messages":[{"role":"user","content":"x"*chars}], "max_tokens": 1}, model="genesys-pi-enterprise")
    msg = (err or {}).get("error", {}).get("message") if isinstance(err, dict) else None
    code = (err or {}).get("error", {}).get("code") if isinstance(err, dict) else None
    pt = (usage or {}).get("prompt_tokens")
    out["context_limits"][chars] = {"status": st, "code": code, "message": (msg or "")[:160], "prompt_tokens": pt}
    print(f"  {chars:>9} chars -> HTTP {st} code={code} pt={pt} {(msg or '')[:90]!r}")
    time.sleep(0.3)

print("\n== EXTRA PARAMS: accepted (200) vs rejected (code) ==")
for p, v in [("min_p",0.1),("top_k",40),("repetition_penalty",1.1),("enable_thinking",True),
             ("reasoning_effort","high"),("seed",7),("stop",["\n"]),("response_format",{"type":"json_object"})]:
    st, err, dt, clen, usage = C.lua_raw_timed(
        {"messages":[{"role":"user","content":"hi"}], "max_tokens": 2, p: v}, model="genesys-pi-enterprise")
    code = (err or {}).get("error", {}).get("code") if isinstance(err, dict) else None
    out["extra_params"][p] = {"status": st, "code": code, "accepted": st == 200}
    print(f"  {p:20} -> HTTP {st} {'ACCEPTED' if st==200 else 'code='+str(code)}")
    time.sleep(0.2)

C.save("gateway", out)
print("\nsaved -> results/gateway.latest.json")
