#!/usr/bin/env python3
"""Prepare one pinned model under the outer supervisor's billing lease."""
import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from b300_remote import execute, upload
import run_b300_campaign as campaign
from b300_tuning import probe_rate

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / 'results-v4/_b300_campaign/migration-20261017'


def local(command, timeout):
    proc = subprocess.Popen([sys.executable, str(ROOT/'scripts'/command[0]), *command[1:]],
                            start_new_session=True)
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        campaign.stop_sprint_tree(proc, grace=5)
        return 124


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', choices=campaign.SLUGS)
    ap.add_argument('--already-downloaded', action='store_true')
    a = ap.parse_args()
    if not campaign.conditional_ready(a.slug):
        return 3
    q = next(q for q in campaign.CAMP['queue'] if q['slug'] == a.slug)
    revisions = json.loads((EVIDENCE/'checkpoints.json').read_text())
    revision = next(x['revision'] for x in revisions if x['slug'] == a.slug)
    card = ROOT/'results-v4/_b300_campaign/model-cards'/f'{a.slug}.md'
    if not card.is_file():
        raise RuntimeError('Official model card must be reviewed before launch')
    # Credentials remain private; never emit the generated config or key.
    options_path = ROOT/'config/opencode.benchmark.json'
    options = json.loads(options_path.read_text())
    key = options['provider']['runpod-vllm']['options']['apiKey']
    upload(key.encode(), '/root/.vllm_key')
    upload((ROOT/'scripts/b300_serve.py').read_bytes(), '/root/b300_serve.py')
    # Reapply the recorded parser repair after an empty-volume pod migration.
    # This happens before server launch; never hot-replace a running parser.
    upload((ROOT/'scripts/b300_patch_qwen_parser.py').read_bytes(),
           '/root/b300_patch_qwen_parser.py')
    parser_patch = execute('/root/venv/bin/python /root/b300_patch_qwen_parser.py', timeout=20)
    (EVIDENCE/f'parser-patch-{a.slug}-{time.time_ns()}.json').write_text(parser_patch)
    # Archive the exact deletion plan locally before removing any re-downloadable
    # weights. All config, caches, model workspaces and paused state stay intact.
    upload(json.dumps(campaign.CAMP).encode(), '/root/campaign.json')
    if not a.already_downloaded:
        upload((ROOT/'scripts/b300_weight_space.py').read_bytes(), '/root/b300_weight_space.py')
        upload((EVIDENCE/'checkpoints.json').read_bytes(), '/root/checkpoints.json')
        removal=execute('python3 /root/b300_weight_space.py '+a.slug)
        (EVIDENCE/f'weight-removal-plan-{a.slug}-{time.time_ns()}.json').write_text(removal)
        applied=execute('python3 /root/b300_weight_space.py '+a.slug+' --apply')
        (EVIDENCE/f'weight-removal-applied-{a.slug}-{time.time_ns()}.json').write_text(applied)
        download_started=time.time()
        stamp = str(time.time_ns())
        script = ('#!/bin/bash\nset -uo pipefail\n'
                  'export HF_TOKEN="$(cat /root/.cache/huggingface/token 2>/dev/null)"\n'
                  f'/root/venv/bin/hf download {shlex.quote(q["hf_repo"])} --revision {revision} '
                  f'--local-dir /root/models/{q["local_dir"]}\n'
                  f'echo $? > /root/logs/download-{stamp}.exit\n')
        upload(script.encode(), '/root/download-model.sh', '700')
        upload((ROOT/'scripts/b300_download_control.py').read_bytes(), '/root/b300_download_control.py')
        execute(f'python3 /root/b300_download_control.py start {stamp}')
        deadline = time.time()+3600
        last_progress=time.time()
        progress=None
        while time.time() < deadline:
            result = execute(f'if test -f /root/logs/download-{stamp}.exit; then cat /root/logs/download-{stamp}.exit; else kill -0 $(cat /root/logs/download-{stamp}.pid) 2>/dev/null || echo dead; fi', timeout=15).strip()
            if result:
                (EVIDENCE/f'download-{a.slug}-{stamp}.log').write_text(execute(f'cat /root/logs/download-{stamp}.log'))
                if result != '0':
                    raise RuntimeError('Pinned model download failed')
                break
            sample=execute(f'du -sb /root/models/{q["local_dir"]} 2>/dev/null; stat -c %s /root/logs/download-{stamp}.log',timeout=15).strip()
            if sample!=progress:
                progress=sample;last_progress=time.time()
            elif time.time()-last_progress>300:
                (EVIDENCE/f'download-{a.slug}-{stamp}-stalled.log').write_text(execute(f'cat /root/logs/download-{stamp}.log'))
                raise TimeoutError('No weight-download or log progress for five minutes')
            print('Download active; bounded progress check passed',flush=True)
            time.sleep(15)
        else:
            (EVIDENCE/f'download-{a.slug}-{stamp}-timeout.log').write_text(execute(f'cat /root/logs/download-{stamp}.log'))
            raise TimeoutError('Download deadline')
        ledger=campaign.load_ledger()
        campaign.annotate(a.slug,'download',time.time()-download_started,ledger)
    # One tunnel per restored pod, no unowned process termination.
    tunnel = execute('test ! -f /root/logs/tunnel.pid || cat /root/logs/tunnel.pid').strip()
    if not tunnel:
        execute('nohup /root/cloudflared tunnel --url http://localhost:8000 --no-autoupdate > /root/logs/tunnel.log 2>&1 < /dev/null & echo $! > /root/logs/tunnel.pid')
    url = None
    for _ in range(8):
        log = execute('cat /root/logs/tunnel.log')
        matches = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', log)
        if matches:
            url = matches[-1]+'/v1'
            break
        time.sleep(3)
    if not url:
        raise RuntimeError('Tunnel URL unavailable')
    options['provider']['runpod-vllm']['options']['baseURL'] = url
    options_path.write_text(json.dumps(options, indent=2)+'\n')
    options_path.chmod(0o600)
    config = json.loads((ROOT/'config/b300_campaign.json').read_text())
    if not config['billing_safety']['paid_execution_enabled']:
        raise RuntimeError('Billing guard not admitted')
    base = q['serve_args']
    # Preserve GLM's accepted attempt settings; migration is revalidation, not a
    # new opportunity to alter the kit midway through the benchmark.
    resumed = bool(list((campaign.OUT/a.slug/'sprints').glob('*/sprint.result.json')))
    candidates = [base]
    text = card.read_text()
    if not resumed:
        if '--language-model-only' in text and '--language-model-only' not in base:
            base += ' --language-model-only'
            candidates[0] = base
        spec = re.search(r"--speculative-config\s+'([^']+)'", text)
        if spec and 'flash_next' not in a.slug:
            try:
                json.loads(spec[1])
                candidates.append(base+' --speculative-config '+shlex.quote(spec[1]))
            except ValueError:
                pass
        if a.slug == 'v2_glm_4_7_flash_bf16_oss':
            candidates.append(base+" --speculative-config '{\"method\":\"mtp\",\"num_speculative_tokens\":1}'")
        if a.slug == 'v2_nemotron35_super_vl_oss':
            candidates.append(base+" --speculative-config '{\"method\":\"mtp\",\"num_speculative_tokens\":3}'")
        if a.slug == 'v2_muse_glimmer_30b_oss':
            candidates.append(base+" --speculative-config '{\"method\":\"dflash\",\"model\":\"/root/models/muse-glimmer-assistant\",\"num_speculative_tokens\":15}'")
        for size in (1024, 2048):
            if len(candidates) < 3:
                candidates.append(base+f' --max-num-batched-tokens {size}')
    tuning_started=time.time()
    if not resumed and q.get('recovery_candidates'):
        candidates=list(q['recovery_candidates'])[:3]
    deadline = tuning_started+2700
    if q.get('runtime_venv') == '/root/venv-nemotron032':
        upload((ROOT/'scripts/b300_nemotron_runtime.sh').read_bytes(), '/root/b300_nemotron_runtime.sh')
        execute('timeout -k 30 1200 bash /root/b300_nemotron_runtime.sh > /root/logs/nemotron032-setup.log 2>&1',timeout=1250)
        (EVIDENCE/'nemotron032-packages.txt').write_text(execute('cat /root/logs/nemotron032-packages.txt'))
        (EVIDENCE/'nemotron032-setup.log').write_text(execute('cat /root/logs/nemotron032-setup.log'))
    trials=[]
    for index,args in enumerate(candidates[:3]):
        if time.time() >= deadline:
            break
        if '/root/models/muse-glimmer-assistant' in args:
            execute('timeout -k 15 180 /root/venv/bin/hf download meta-models/Muse-Glimmer-30B-assistant --revision e8192f3a8f617f74be2ce220360c89ef4789f39f --local-dir /root/models/muse-glimmer-assistant > /root/logs/muse-assistant-download.log 2>&1',timeout=200)
            (EVIDENCE/'muse-assistant-download.log').write_text(execute('cat /root/logs/muse-assistant-download.log'))
        # Persist actual settings before every launch: fingerprint and reproduction
        # use exactly the same config as the pod, with no context/reasoning changes.
        selected = next(x for x in config['queue'] if x['slug']==a.slug)
        selected['serve_args']=args
        (ROOT/'config/b300_campaign.json').write_text(json.dumps(config,indent=2)+'\n')
        campaign.CAMP=config
        upload(json.dumps(config).encode(), '/root/campaign.json')
        execute('python3 /root/b300_serve.py stop')
        execute('python3 /root/b300_serve.py '+a.slug)
        marker=time.time()
        remaining=lambda: max(1,int(deadline-time.time()))
        rc=local(['b300_start_sprint.py',a.slug,'--preflight-only','--ready-timeout',str(min(1800,max(1,remaining()-360)))],remaining())
        if not rc:
            rc=local(['b300_perf_probe.py',a.slug,'--label',f'restored-pod-{index}'],min(330,remaining()))
        trial=dict(index=index,serve_args=args,exit_code=rc,started_at=marker,
                   finished_at=time.time(),passed=False)
        def latest(pattern):
            paths=[p for p in EVIDENCE.glob(pattern) if p.stat().st_mtime>=marker]
            return max(paths,key=lambda p:p.stat().st_mtime) if paths else None
        probe=latest(f'perf-{a.slug}-restored-pod-{index}-*.json')
        preflight=latest(f'preflight-{a.slug}-*.json')
        if not rc and probe and preflight:
            rate=probe_rate(json.loads(probe.read_text()))
            passed=rate>=100 and json.loads(preflight.read_text()).get('passed') is True and time.time()<=deadline
            trial.update(passed=passed,decode_tokens_per_second=rate,
                         tool_preflight_passed=True,serving_fingerprint=campaign.serving_fingerprint(a.slug),
                         evidence=[str(p.relative_to(ROOT)) for p in (probe,preflight,card)],
                         revision=revision)
            if passed:
                dest=ROOT/'results-v4/_b300_campaign/performance-validation'/f'{a.slug}.json'
                dest.parent.mkdir(exist_ok=True)
                if dest.exists():dest.rename(dest.with_name(f'{a.slug}-prior-{time.time_ns()}.json'))
                dest.write_text(json.dumps(trial,indent=2)+'\n')
        trials.append(trial)
        (EVIDENCE/f'new-pod-tuning-{a.slug}.json').write_text(json.dumps(dict(
            trials=trials,deadline=deadline,resumed_frozen_recipe=resumed,
            official_card=str(card.relative_to(ROOT)),
            research_source='https://docs.vllm.ai/en/latest/configuration/optimization/',
            rationale='Native MTP when model card supplies recipe; otherwise bounded smaller prefill batch tests for latency. No context/output/reasoning reduction.'),indent=2)+'\n')
        local(['b300_archive_server.py',a.slug,'--label',f'new-pod-trial-{index}'],min(180,remaining()))
        if trial['passed']:
            ledger=campaign.load_ledger()
            campaign.annotate(a.slug,'serve_load',time.time()-tuning_started,ledger)
            print(json.dumps({'slug':a.slug,'decode_tokens_per_second':trial['decode_tokens_per_second'],'passed':True}),flush=True)
            return 0
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
