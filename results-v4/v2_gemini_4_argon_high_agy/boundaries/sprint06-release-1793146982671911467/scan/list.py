import json,sys,re
f=sys.argv[1]
for l in open(f):
    e=json.loads(l)
    for tc in e.get('tool_calls') or []:
        a=tc.get('args',{})
        s=a.get('CommandLine') or a.get('Path') or a.get('AbsolutePath') or a.get('TargetFile') or json.dumps(a)[:160]
        print(e.get('step_index'), tc.get('name'), str(s)[:230].replace('\n',' '))
