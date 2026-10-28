import json,sys,re
for l in open(sys.argv[1]):
    e=json.loads(l)
    if e.get('step_index') in (223,224):
        s=json.dumps(e)
        for m in re.finditer(r'\d+ runs, \d+ assertions, \d+ failures, \d+ errors, \d+ skips|no warnings|No vulnerabilities found|Security Warnings: \d+|\d+ files inspected, [^"\\]*',s): print(e['step_index'],m.group(0))
