#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["harbor==0.23.0"]
# ///
"""Run the pinned FrontierSWE extension of v4.1 through Harbor/Docker.

Original tasks, separate verifiers, one attempt, no implicit model retries.
Validate oracle and baseline controls before running any model. Raw jobs stay local.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "benchmark-v4.1/frontier/manifest.json"


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def summarize_result(result: dict) -> dict:
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    reward = rewards.get("reward")
    error = result.get("exception_info")
    budget_exhausted = (error or {}).get("exception_type") == "AgentTimeoutError"
    valid = ((not error or budget_exhausted) and rewards.get("valid") == 1
             and isinstance(reward, (int, float)) and math.isfinite(reward) and 0 <= reward <= 1)
    return dict(status="completed" if valid else "error", reward=reward,
                score=100 * reward if valid else None, rewards=rewards, exception_info=error,
                budget_exhausted=budget_exhausted)


def checkout(manifest: dict) -> Path:
    path = ROOT / "tmp/frontier-swe-v2"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", manifest["repository"], str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "checkout", "--detach", manifest["revision"]], check=True)
    revision = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True).strip()
    if revision != manifest["revision"] or dirty:
        raise RuntimeError("Upstream checkout must be clean and at the manifest revision")
    for name, spec in manifest["tasks"].items():
        for filename, expected in spec["sha256"].items():
            actual = hashlib.sha256((path / "tasks" / name / filename).read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError(f"Upstream hash mismatch: {name}/{filename}")
    return path


def build_config(task: Path, spec: dict, manifest: dict, args):
    from harbor.models.job.config import JobConfig
    from harbor.models.trial.config import AgentConfig, EnvironmentConfig, TaskConfig, VerifierConfig

    environment = EnvironmentConfig(
        type="docker", env={"TASK_BUDGET_SECS": "72000"},
        extra_docker_compose=[ROOT / "benchmark-v4.1/frontier/docker-network.yaml"],
    )
    verifier = VerifierConfig()
    if args.memory_mb:
        environment.override_memory_mb = args.memory_mb
    if args.mode == "oracle":
        flag = uuid.uuid4().hex
        environment.env["HARBOR_ORACLE_FLAG"] = flag
        verifier.env["HARBOR_ORACLE_FLAG"] = flag
        agent = AgentConfig(name="oracle")
    elif args.mode == "baseline":
        agent = AgentConfig(name="nop")
    elif args.mode in ("astra", "fable"):
        astra = args.mode == "astra"
        agent = AgentConfig(
            import_path="frontier_native:" + ("FrontierCodex" if astra else "FrontierClaude"),
            model_name="gpt-6-astra" if astra else "claude-fable-5-1",
            env={},
            extra_allowed_hosts=(["chatgpt.com", "auth.openai.com"] if astra else
                                 ["api.anthropic.com", "claude.ai", "platform.claude.com"]),
            kwargs=({"version": "0.156.0", "reasoning_effort": "high", "web_search": "disabled"}
                    if astra else {"version": "2.1.280"}),
        )
    else:
        if not os.environ.get("LUA_API_KEY"):
            raise RuntimeError("LUA_API_KEY must be set; credentials are never copied from the host config")
        agent = AgentConfig(
            import_path="frontier_opencode:FrontierOpenCode", model_name="lua/genesys-pi-house",
            env={"LUA_API_KEY": "${LUA_API_KEY}", "OPENCODE_DISABLE_AUTOUPDATE": "true"},
            extra_allowed_hosts=["api.lua.vision"],
            kwargs={"version": manifest["opencode_version"], "opencode_config": {
                "provider": {"lua": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "LUA Vision",
                    "options": {"baseURL": "https://api.lua.vision/v1", "apiKey": "{env:LUA_API_KEY}"},
                    "models": {"genesys-pi-house": {
                        "id": "genesys-pi-house", "name": "Genesys PI House", "tool_call": True,
                        "reasoning": True, "limit": {"context": 600000, "output": 128000},
                    }},
                }},
            }},
        )
    return JobConfig(
        job_name=f"{args.mode}-{task.name}-{uuid.uuid4().hex[:8]}",
        jobs_dir=ROOT / "results-v4.1/frontier/jobs",
        tasks=[TaskConfig(path=task)], agents=[agent], environment=environment,
        verifier=verifier, n_attempts=1, n_concurrent_trials=1,
    )


async def run(args) -> int:
    from harbor.job import Job

    manifest = json.loads(MANIFEST.read_text())
    source = checkout(manifest)
    names = args.task or list(manifest["tasks"])
    for name in names:
        spec = manifest["tasks"][name]
        out = ROOT / "results-v4.1/frontier" / name
        out.mkdir(parents=True, exist_ok=True)
        config = build_config(source / "tasks" / name, spec, manifest, args)
        if args.mode in ("genesys", "astra", "fable") and not args.dry_run:
            for control in ("oracle", "baseline"):
                evidence = out / f"{control}.json"
                validation = json.loads(evidence.read_text()) if evidence.exists() else {}
                if (not validation.get("validated") or validation.get("revision") != manifest["revision"]
                        or validation.get("memory_mb") != (args.memory_mb or spec["memory_mb"])):
                    raise RuntimeError(f"Run and validate {control} at the same memory limit first: {name}")
        provenance = {
            "revision": manifest["revision"], "task": name, "mode": args.mode,
            "model": config.agents[0].model_name,
            "harness": {"genesys": "Harbor OpenCode", "astra": "Harbor Codex", "fable": "Harbor Claude Code"}.get(args.mode, args.mode),
            "native_version": config.agents[0].kwargs.get("version"),
            "harbor_version": manifest["harbor_version"], "opencode_version": manifest["opencode_version"],
            "agent_image": spec["agent_image"], "verifier_image": spec["verifier_image"],
            "memory_mb": args.memory_mb or spec["memory_mb"],
            "resource_deviation": bool(args.memory_mb and args.memory_mb != spec["memory_mb"]),
            "job_dir": str(config.jobs_dir / config.job_name), "status": "prepared",
            "started_at": datetime.now(timezone.utc).isoformat(), "runner_pid": os.getpid(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "adapter_sha256": hashlib.sha256((ROOT / ("scripts/frontier_native.py" if args.mode in ("astra", "fable") else "scripts/frontier_opencode.py")).read_bytes()).hexdigest(),
        }
        if args.dry_run:
            print(json.dumps(provenance, indent=2))
            continue
        record = out / f"{args.mode}.json"
        if record.exists() and args.mode in ("genesys", "astra", "fable"):
            raise RuntimeError(f"Refusing to overwrite an existing model attempt: {record}")
        write_json(record, provenance)
        print(f"START {name}: {args.mode}; job={config.job_name}", flush=True)
        try:
            job = await Job.create(config)
            await job.run()
            trial_files = list((config.jobs_dir / config.job_name).glob("*/result.json"))
            if len(trial_files) != 1:
                raise RuntimeError(f"Expected one trial result, got {len(trial_files)}")
            result = json.loads(trial_files[0].read_text())
            provenance.update(summarize_result(result), result_path=str(trial_files[0]))
            reward = provenance["reward"]
            if args.mode in ("oracle", "baseline"):
                expected = spec["oracle_expected"] if args.mode == "oracle" else 0
                provenance["validated"] = provenance["status"] == "completed" and abs(reward - expected) < 0.001
            provenance["finished_at"] = datetime.now(timezone.utc).isoformat()
            write_json(record, provenance)
            print(f"DONE {name}: {provenance['status']} reward={reward}", flush=True)
            if provenance["status"] != "completed" or (args.mode in ("oracle", "baseline") and not provenance["validated"]):
                return 1
        except BaseException:
            provenance["status"] = "interrupted_or_error"
            write_json(record, provenance)
            raise
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["oracle", "baseline", "genesys", "astra", "fable"], required=True)
    parser.add_argument("--task", action="append", choices=list(json.loads(MANIFEST.read_text())["tasks"]))
    parser.add_argument("--memory-mb", type=int, help="Explicit local resource deviation, recorded in results")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.memory_mb is not None and args.memory_mb <= 0:
        parser.error("--memory-mb must be positive")
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
