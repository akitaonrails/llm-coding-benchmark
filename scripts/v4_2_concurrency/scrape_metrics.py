#!/usr/bin/env python3
"""v4.2: sample vLLM /metrics over time during a concurrency ramp.

Run ON the pod (against localhost:8000/metrics) in the background while the ramp runs:
    python3 scrape_metrics.py --url http://localhost:8000/metrics \
        --out /root/v4.2_results/<model>/metrics_timeline.jsonl --interval 2

Captures the Prometheus gauges that explain capacity: KV-cache utilization,
running vs waiting sequences, preemptions, and throughput counters. One JSON
object per sample. Stdlib only. Stop with SIGINT/SIGTERM (flushes).
"""
import argparse, json, time, urllib.request, signal, sys

# gauge/counter name -> key in our record (vLLM metric names may carry a suffix; match by prefix)
WANT = {
    "vllm:gpu_cache_usage_perc": "kv_cache_util",
    "vllm:num_requests_running": "running",
    "vllm:num_requests_waiting": "waiting",
    "vllm:num_requests_swapped": "swapped",
    "vllm:num_preemptions": "preemptions_total",
    "vllm:prompt_tokens_total": "prompt_tokens_total",
    "vllm:generation_tokens_total": "generation_tokens_total",
}

def parse_prom(text):
    out = {}
    for line in text.splitlines():
        if not line or line[0] == "#":
            continue
        # metric{labels} value   OR   metric value
        name = line.split("{", 1)[0].split(" ", 1)[0]
        for prefix, key in WANT.items():
            if name == prefix:
                try:
                    val = float(line.rsplit(" ", 1)[1])
                except (IndexError, ValueError):
                    continue
                # several TP ranks/labels -> sum counters, max the utilization gauge
                if key == "kv_cache_util":
                    out[key] = max(out.get(key, 0.0), val)
                else:
                    out[key] = out.get(key, 0.0) + val
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/metrics")
    ap.add_argument("--out", required=True)
    ap.add_argument("--interval", type=float, default=2.0)
    a = ap.parse_args()

    f = open(a.out, "a")
    running = {"stop": False}
    def _stop(*_):
        running["stop"] = True
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    while not running["stop"]:
        rec: dict = {"t": time.time()}
        try:
            with urllib.request.urlopen(a.url, timeout=5) as r:
                rec.update(parse_prom(r.read().decode("utf-8", "replace")))
        except Exception as e:
            rec["err"] = type(e).__name__
        f.write(json.dumps(rec) + "\n")
        f.flush()
        time.sleep(a.interval)
    f.close()
    print("scrape_metrics: stopped", file=sys.stderr)

if __name__ == "__main__":
    main()
