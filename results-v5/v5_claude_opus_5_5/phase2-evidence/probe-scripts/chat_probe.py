"""Drive one chat turn: subscribe via Action Cable to the conversation's Turbo
Stream, POST a message, and log every broadcast with a timestamp."""
import asyncio, json, re, sys, time, html, aiohttp

BASE = sys.argv[1]
PROMPTS = sys.argv[2:]
JAR = "/tmp/p2-scripts/cookies.json"

async def main():
    jar = aiohttp.CookieJar(unsafe=True)
    try:
        jar.load(JAR)
    except Exception:
        pass
    async with aiohttp.ClientSession(cookie_jar=jar, connector=aiohttp.TCPConnector(force_close=True)) as s:
        conv = None
        try:
            conv = open("/tmp/p2-scripts/conv").read().strip()
        except Exception:
            pass
        url = f"{BASE}/conversations/{conv}" if conv else f"{BASE}/"
        async with s.get(url) as r:
            page = await r.text(); conv = str(r.url).rstrip("/").split("/")[-1]
        open("/tmp/p2-scripts/conv", "w").write(conv)
        signed = html.unescape(re.search(r'signed-stream-name="([^"]+)"', page).group(1))
        csrf = re.search(r'name="csrf-token" content="([^"]+)"', page).group(1)
        print(f"conversation={conv}")
        ws = await s.ws_connect(f"{BASE.replace('http', 'ws')}/cable", headers={"Origin": BASE})
        ident = json.dumps({"channel": "Turbo::StreamsChannel", "signed_stream_name": signed})
        await ws.send_str(json.dumps({"command": "subscribe", "identifier": ident}))
        while True:
            m = json.loads((await ws.receive()).data)
            if m.get("type") == "confirm_subscription": break
        for prompt in PROMPTS:
            t0 = time.monotonic()
            async with s.post(f"{BASE}/conversations/{conv}/messages",
                              data={"message[content]": prompt, "authenticity_token": csrf},
                              headers={"Accept": "text/vnd.turbo-stream.html"}) as r:
                print(f"POST status={r.status} at +{time.monotonic()-t0:.3f}s")
            chunks = 0
            done = False
            while not done:
                try:
                    msg = await ws.receive(timeout=180)
                except asyncio.TimeoutError:
                    print("TIMEOUT"); break
                d = json.loads(msg.data)
                if d.get("type") in ("ping", "welcome"): continue
                frag = d.get("message", "")
                act = re.search(r'action="(\w+)" target="([^"]+)"', frag)
                body = re.sub(r"<[^>]+>", "", frag)
                body = re.sub(r"\s+", " ", body).strip()
                a, tgt = (act.group(1), act.group(2)) if act else ("?", "?")
                if a == "append" and tgt.endswith("_body"): chunks += 1
                print(f"+{time.monotonic()-t0:7.3f}s {a:8s} {tgt:45s} {body[:110]!r}")
                if tgt == "token_usage" or (a == "replace" and tgt.startswith("assistant_turn") and "notice" in frag.lower()):
                    done = True
            print(f"== streamed body chunks: {chunks}\n")
        await ws.close()
    jar.save(JAR)

asyncio.run(main())
