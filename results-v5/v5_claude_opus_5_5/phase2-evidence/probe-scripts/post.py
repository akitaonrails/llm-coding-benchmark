import re, sys, json, urllib.request, urllib.parse
jar = json.load(open("/tmp/p2-scripts/cookies.json"))
cookie = "; ".join(f"{k}={v['value']}" for d in jar.values() for k, v in d.items())
conv = open("/tmp/p2-scripts/conv").read().strip()
page = urllib.request.urlopen(urllib.request.Request(f"{sys.argv[1]}/conversations/{conv}", headers={"Cookie": cookie})).read().decode()
csrf = re.search(r'name="csrf-token" content="([^"]+)"', page).group(1)
data = urllib.parse.urlencode({"message[content]": sys.argv[2], "authenticity_token": csrf}).encode()
try:
    r = urllib.request.urlopen(urllib.request.Request(f"{sys.argv[1]}/conversations/{conv}/messages", data=data, headers={"Cookie": cookie, "Accept": "text/vnd.turbo-stream.html"}))
    print("POST", r.status)
except urllib.error.HTTPError as e:
    print("POST", e.code, re.sub(r"<[^>]+>|\s+", " ", e.read().decode())[:160])
