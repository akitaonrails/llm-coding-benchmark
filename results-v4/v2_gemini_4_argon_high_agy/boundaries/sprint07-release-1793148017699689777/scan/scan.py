import json,sys,re,collections
f=sys.argv[1]
pat=re.compile(r'CLAUDE\.md|AGENTS\.md|rubric|audit_prompt|bench_shield|v4shield|success_report|benchmark-audit|benchmark-v4|sabotage|INJECTION|grade\.json|boundaries|\.\./\.\.|v2_(?!gemini_4_argon_high_agy)[a-z0-9_]+',re.I)
proj='/mnt/data/Projects/llm-coding-benchmark/results-v4/v2_gemini_4_argon_high_agy/project'
kinds=collections.Counter(); hits=[]; outhits=0; first=last=None; n=0; cmds=[]
for i,l in enumerate(open(f)):
    try: e=json.loads(l)
    except: continue
    s=json.dumps(e)
    ts=re.search(r'"(?:timestamp|created_at|time)"\s*:\s*"([^"]+)"',s)
    if ts:
        first=first or ts.group(1); last=ts.group(1)
    # tool inputs
    def walk(o,path=''):
        if isinstance(o,dict):
            for k,v in o.items(): yield from walk(v,path+'/'+k)
        elif isinstance(o,list):
            for x in o: yield from walk(x,path)
        else: yield path,o
    for p,v in walk(e):
        if not isinstance(v,str): continue
        low=p.lower()
        isinput=any(k in low for k in ('args','input','arguments','command','commandline','toolcall','tool_call','path')) and 'output' not in low and 'result' not in low
        for m in pat.finditer(v):
            if isinput: hits.append((i,p,m.group(0),v[:200]))
            else: outhits+=1
        if isinput:
            for ab in re.findall(r'/(?:mnt|home|tmp|root|etc)/[^\s"\']+',v):
                if not ab.startswith(proj): hits.append((i,p,'ABS',ab[:150]))
    for k in ('name','tool_name','toolName'):
        if isinstance(e.get(k),str): kinds[e[k]]+=1
print('lines',i+1,'first',first,'last',last)
print('top-level keys sample',list(e.keys())[:10])
print('kinds',kinds.most_common(20))
print('input hits',len(hits))
for h in hits[:40]: print(h)
print('output/prose pattern hits',outhits)
