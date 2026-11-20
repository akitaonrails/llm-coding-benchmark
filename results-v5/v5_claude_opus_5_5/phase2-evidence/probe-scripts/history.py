import re, sys, html, json, urllib.request
jar = json.load(open("/tmp/p2-scripts/cookies.json"))
cookie = "; ".join(f"{k}={v['value']}" for d in jar.values() for k, v in d.items())
conv = open("/tmp/p2-scripts/conv").read().strip()
req = urllib.request.Request(f"{sys.argv[1]}/conversations/{conv}", headers={"Cookie": cookie})
page = urllib.request.urlopen(req).read().decode()
print("title:", html.unescape(re.search(r"<title>(.*?)</title>", page).group(1)))
for role, body in re.findall(r'data-role="(\w+)">\s*<div[^>]*>(.*?)</div>', page, re.S):
    print(role, "|", re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", body))).strip()[:110])
