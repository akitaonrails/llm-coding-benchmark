import concurrent.futures
import http.client
import json
import re
import sys
import time
from html.parser import HTMLParser
from urllib.parse import urlencode, urlsplit

import requests
import websocket


class ChatPage(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.stream = self.csrf = None
        self.feed(html)

    def handle_starttag(self, tag, html_attrs):
        attrs = dict(html_attrs)
        if tag == "turbo-cable-stream-source":
            self.stream = attrs["signed-stream-name"]
        if tag == "meta" and attrs.get("name") == "csrf-token":
            self.csrf = attrs["content"]


class Probe:
    def __init__(self, base, history_path=None):
        self.base = base
        self.address = urlsplit(base)
        self.http = requests.Session()
        response = self.http.get(base + (history_path or "/"), timeout=10)
        response.raise_for_status()
        self.path = urlsplit(response.url).path
        self.page = ChatPage(response.text)
        assert self.page.stream and self.page.csrf
        self.initial_html = response.text
        self.identifier = json.dumps({
            "channel": "Turbo::StreamsChannel",
            "signed_stream_name": self.page.stream,
        })
        print(f"CHAT {self.path}", flush=True)

    def socket(self):
        socket = websocket.create_connection(
            "ws://" + self.address.netloc + "/cable", timeout=115,
            cookie="; ".join(f"{name}={value}" for name, value in self.http.cookies.items()),
            subprotocols=["actioncable-v1-json"],
        )
        assert json.loads(socket.recv())["type"] == "welcome"
        socket.send(json.dumps({"command": "subscribe", "identifier": self.identifier}))
        while True:
            frame = json.loads(socket.recv())
            if frame.get("type") == "confirm_subscription":
                return socket
            assert frame.get("type") == "ping", frame.get("type")

    def post(self, prompt, label):
        response = self.http.post(
            self.base + self.path + "/messages", data={"prompt": prompt}, timeout=115,
            headers={"Accept": "text/vnd.turbo-stream.html", "Origin": self.base,
                     "X-CSRF-Token": self.page.csrf, "X-Request-Id": label},
        )
        return (time.monotonic(), response)

    def send(self, prompt, label, socket=None):
        began = time.monotonic()
        socket = socket or self.socket()
        saw_finish = False
        chunks = []
        with concurrent.futures.ThreadPoolExecutor() as pool:
            submitted_at = time.monotonic()
            pending = pool.submit(self.post, prompt, label)
            while not saw_finish:
                frame = json.loads(socket.recv())
                arrived_at = time.monotonic()
                if frame.get("identifier") != self.identifier or not isinstance(frame.get("message"), str):
                    continue
                message = frame["message"]
                tags = re.findall(r'<turbo-stream\b[^>]+>', message)
                print(f"{label} +{arrived_at-submitted_at:.3f}s POST {'done' if pending.done() else 'pending'} {' '.join(tags)}", flush=True)
                if re.search(r'action="append" target="turn_[a-f0-9]+_reply"', message):
                    chunks.append((arrived_at, not pending.done(), re.search(r"<template>(.*)</template>", message, re.S)[1]))
                saw_finish = 'action="update" target="chat_messages"' in message
            finished, response = pending.result()
        socket.close()
        print(f"{label} +{finished-submitted_at:.3f}s POST HTTP {response.status_code}; {len(chunks)} reply appends", flush=True)
        if not response.ok:
            print("POST error:", re.findall(r'<p[^>]*>(.*?)</p>', response.text, re.S)[-2:], flush=True)
        response.raise_for_status()
        assert all(ts < finished for ts, was_pending, fragment in chunks if was_pending)
        assert chunks, "No reply appends"
        print(f"{label} first append +{chunks[0][0]-submitted_at:.3f}s; last append +{chunks[-1][0]-submitted_at:.3f}s; {sum(pending for _, pending, _ in chunks)} arrived before POST finished", flush=True)
        print(f"{label} reply fragments {''.join(fragment for _, _, fragment in chunks)}", flush=True)
        return chunks


if __name__ == "__main__":
    base = sys.argv[1]
    probe = Probe(base)
    chunks = probe.send(sys.argv[3], sys.argv[2])
    if sys.argv[2] == "streaming":
        assert sum(pending for _, pending, _ in chunks) >= 2
        assert chunks[-1][0] - chunks[0][0] >= 0.1
