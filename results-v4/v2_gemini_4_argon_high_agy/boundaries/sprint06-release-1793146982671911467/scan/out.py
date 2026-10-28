import json,sys,re
pat=re.compile(r'CLAUDE\.md|AGENTS\.md|rubric|audit_prompt|bench_shield|v4shield|success_report|benchmark-audit|benchmark-v4|sabotage|INJECTION|grade\.json|boundaries|v2_(?!gemini_4_argon_high_agy)[a-z0-9_]+',re.I)
for l in open(sys.argv[1]):
    e=json.loads(l)
    s=json.dumps({k:v for k,v in e.items() if k!='tool_calls'})
    for m in pat.finditer(s):
        print(e.get('step_index'),e.get('source'),e.get('type'),repr(s[max(0,m.start()-80):m.end()+60]))
