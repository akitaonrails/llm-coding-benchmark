import asyncio, json, re, sys, time, html, aiohttp
BASE, SECS = sys.argv[1], float(sys.argv[2])
async def main():
    jar = aiohttp.CookieJar(unsafe=True); jar.load("/tmp/p2-scripts/cookies.json")
    conv = open("/tmp/p2-scripts/conv").read().strip()
    async with aiohttp.ClientSession(cookie_jar=jar) as s:
        page = await (await s.get(f"{BASE}/conversations/{conv}")).text()
        signed = html.unescape(re.search(r'signed-stream-name="([^"]+)"', page).group(1))
        ws = await s.ws_connect(f"{BASE.replace('http','ws')}/cable", headers={"Origin": BASE})
        await ws.send_str(json.dumps({"command": "subscribe", "identifier": json.dumps({"channel": "Turbo::StreamsChannel", "signed_stream_name": signed})}))
        end = time.monotonic() + SECS; t0 = time.monotonic()
        while time.monotonic() < end:
            try: d = json.loads((await ws.receive(timeout=end - time.monotonic())).data)
            except Exception: break
            if d.get("type"): print(d["type"], flush=True); continue
            a = re.search(r'action="(\w+)" target="([^"]+)"', d["message"])
            print(f"+{time.monotonic()-t0:6.2f}s {a.group(1)} {a.group(2)}", flush=True)
asyncio.run(main())
