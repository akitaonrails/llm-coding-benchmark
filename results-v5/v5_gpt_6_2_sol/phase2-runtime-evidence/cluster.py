import http.client
import json
import re
import secrets
import subprocess
import sys
from pathlib import Path
from time import monotonic
from urllib.parse import urlencode

from lxml.html import fromstring

from probe import Probe

PORT = 13681
ADDRESS = "127.0.0.1"
STATE = Path("cluster.json")


def worker(socket):
    source_port = socket.getsockname()[1]
    output = subprocess.check_output(
        ["ss", "-Hntp", "state", "established", f"( sport = :{PORT} and dport = :{source_port} )"],
        text=True,
    )
    pids = set(int(value) for value in re.findall(r"pid=(\d+)", output))
    assert len(pids) == 1, output
    return pids.pop()


class Cluster(Probe):
    def choose_connection(self, other_worker=None):
        connections = []
        try:
            for _ in range(20):
                connection = http.client.HTTPConnection(ADDRESS, PORT, timeout=110)
                connection.request("GET", "/up")
                response = connection.getresponse()
                assert response.status == 200
                response.read()
                pid = worker(connection.sock)
                if pid != other_worker:
                    return connection, pid
                connections.append(connection)
            raise AssertionError(f"Could not find another worker besides {other_worker}")
        finally:
            for connection in connections:
                connection.close()

    def send_cross_worker(self, prompt, label):
        socket = self.socket()
        ws_worker = worker(socket.sock)
        connection, http_worker = self.choose_connection(ws_worker)
        print(f"{label} POST worker {http_worker}; Cable worker {ws_worker}", flush=True)
        original_post = self.post

        def post_on_selected_worker(prompt, label):
            body = urlencode({"prompt": prompt})
            cookie = "; ".join(f"{name}={value}" for name, value in self.http.cookies.items())
            connection.request("POST", self.path + "/messages", body, {
                "Accept": "text/vnd.turbo-stream.html", "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self.base, "Cookie": cookie, "X-CSRF-Token": self.page.csrf,
                "X-Request-Id": label,
            })
            response = connection.getresponse()
            text = response.read().decode()
            assert worker(connection.sock) == http_worker
            from requests import Response
            result = Response()
            result.status_code = response.status
            result.encoding = "utf-8"
            result._content = text.encode()
            return monotonic(), result

        self.post = post_on_selected_worker
        try:
            self.send(prompt, label, socket)
        finally:
            self.post = original_post
            connection.close()
            socket.close()
        return sorted((http_worker, ws_worker))

    def read_from_both_workers(self):
        pids = []
        views = []
        for _ in range(2):
            connection, pid = self.choose_connection(pids[0] if pids else None)
            try:
                connection.request("GET", self.path)
                response = connection.getresponse()
                assert response.status == 200
                page = fromstring(response.read())
                assert worker(connection.sock) == pid
            finally:
                connection.close()
            pids.append(pid)
            views.append({
                "messages": [div.text_content() for div in page.xpath('//*[@id="chat_messages"]//article/div')],
                "title": page.get_element_by_id("conversation_title").text_content(),
                "usage": page.get_element_by_id("token_usage").text_content(),
            })
        assert views[0] == views[1], views
        print(f"Identical rendered messages, title, and usage from workers {sorted(pids)}: {json.dumps(views[0])}", flush=True)
        return sorted(pids), views[0]


if sys.argv[1] == "before":
    probe = Cluster(f"http://{ADDRESS}:{PORT}")
    nonce = "maple-" + secrets.token_hex(5)
    first_prompt = f"For this conversation, remember the reference code {nonce}. Reply with just Acknowledged."
    second_prompt = "Reply with just READY. Keep the reference code in mind."
    pids = probe.send_cross_worker(first_prompt, "cluster-first")
    assert probe.send_cross_worker(second_prompt, "cluster-second") == pids
    seen_pids, view = probe.read_from_both_workers()
    assert pids == seen_pids
    assert len(view["messages"]) == 4
    assert view["messages"][::2] == [first_prompt, second_prompt]
    STATE.write_text(json.dumps({"path": probe.path, "nonce": nonce, "view": view, "workers": pids}))
else:
    before = json.loads(STATE.read_text())
    probe = Cluster(f"http://{ADDRESS}:{PORT}", before["path"])
    pids, view = probe.read_from_both_workers()
    assert set(pids).isdisjoint(before["workers"])
    assert view == before["view"]
    print("All four original messages, title and usage survived with two new workers", flush=True)
    assert probe.send_cross_worker("What was the reference code I asked you to remember? Reply only with that code.", "cluster-recall") == pids
    seen_pids, continued = probe.read_from_both_workers()
    assert seen_pids == pids
    assert len(continued["messages"]) == 6
    assert continued["messages"][:4] == view["messages"]
    assert before["nonce"] in continued["messages"][-1]
    print(f"Replayed reference code {before['nonce']} and saved the continued turn across both new workers", flush=True)
