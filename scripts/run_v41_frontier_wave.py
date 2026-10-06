#!/usr/bin/env python3
"""Serial P4–P6 queue, completing each model before starting the next. Run with the same Python environment as the runner.

Reuses completed controls and waits for existing attempts instead of launching
duplicates. Stops on infrastructure errors. Does not retry scored model runs.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from run_v41_frontier import MANIFEST, ROOT, summarize_result, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cranelift-memory-mb", type=int)
    parser.add_argument("--models", nargs="+", choices=["genesys", "astra", "fable"], default=["genesys"])
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    out = ROOT / "results-v4.1/frontier"
    out.mkdir(parents=True, exist_ok=True)
    state = out / ("queue.json" if args.models == ["genesys"] else "anchors-queue.json")
    for model, task in [(model, task) for model in args.models for task in manifest["tasks"]]:
        spec = manifest["tasks"][task]
        memory = args.cranelift_memory_mb if task == "cranelift-codegen-opt" else None
        for mode in ("oracle", "baseline", model):
            write_json(state, {"status": "running", "task": task, "phase": mode})
            record = out / task / f"{mode}.json"
            print(f"QUEUE {task} / {mode}", flush=True)
            deadline = time.monotonic() + 26 * 3600
            while record.exists():
                try:
                    data = json.loads(record.read_text())
                except json.JSONDecodeError:
                    # Compatibility with an older runner writing its final record.
                    if time.monotonic() > deadline:
                        raise
                    time.sleep(1)
                    continue
                if data.get("status") != "prepared":
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError(f"Existing attempt never completed: {record}")
                time.sleep(30)
            if not record.exists():
                command = [sys.executable, str(ROOT / "scripts/run_v41_frontier.py"),
                           "--mode", mode, "--task", task]
                if memory:
                    command += ["--memory-mb", str(memory)]
                subprocess.run(command, cwd=ROOT)
            data = json.loads(record.read_text())
            # Reconcile runs started by an older controller using the original
            # Harbor result. An exhausted agent budget still gets graded.
            if mode in ("genesys", "astra", "fable") and data.get("result_path"):
                data.update(summarize_result(json.loads(Path(data["result_path"]).read_text())))
                write_json(record, data)
            if (data.get("status") != "completed" or data.get("revision") != manifest["revision"]
                    or data.get("memory_mb") != (memory or spec["memory_mb"])
                    or (mode in ("oracle", "baseline") and not data.get("validated"))):
                raise RuntimeError(f"Invalid or failed {mode} result; inspect {record}")
            print(f"QUEUE OK {task} / {mode}: {data.get('score')}", flush=True)
    write_json(state, {"status": "completed"})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        state = ROOT / "results-v4.1/frontier" / ("anchors-queue.json" if "--models" in sys.argv else "queue.json")
        data = json.loads(state.read_text()) if state.exists() else {}
        data.update(status="error", error=str(error))
        write_json(state, data)
        raise
