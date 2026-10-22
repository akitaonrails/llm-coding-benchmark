#!/usr/bin/env python3
"""Replace an old fixed-deadline supervisor without restarting its owned sprint."""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
import run_b300_campaign as campaign

class AdoptedProcess:
    def __init__(self,pid):
        self.pid=pid
        self.identity=campaign.process_identity(pid)
        if not self.identity or self.identity[2]=='Z':raise RuntimeError('Runner is not live')
    def poll(self):
        now=campaign.process_identity(self.pid)
        return None if now and now[1]==self.identity[1] and now[2]!='Z' else 0
    def wait(self,timeout=None):
        deadline=time.monotonic()+timeout if timeout is not None else None
        while self.poll() is None:
            if deadline is not None and time.monotonic()>=deadline:
                raise subprocess.TimeoutExpired('adopted sprint',timeout)
            time.sleep(0.1)
        return 0

def argv(pid):return Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('slug');ap.add_argument('--sprint',required=True)
    ap.add_argument('--old-guard',type=int,required=True);ap.add_argument('--runner',type=int,required=True);a=ap.parse_args()
    old=campaign.process_identity(a.old_guard);proc=AdoptedProcess(a.runner)
    if not old or proc.identity[0]!=a.old_guard:raise RuntimeError('Ownership mismatch')
    oldargs=argv(a.old_guard);args=argv(a.runner)
    if not oldargs[1].endswith(b'/run_b300_campaign.py') or a.slug.encode() not in oldargs:raise RuntimeError('Unexpected guard')
    if not args[1].endswith(b'/run_v4_sprint.py') or a.slug.encode() not in args or a.sprint.encode() not in args:raise RuntimeError('Unexpected runner')
    ledger=campaign.LEDGER
    if not ledger.exists():
        matches=list(campaign.REPO.parent.glob('.v4shield_*/results/_b300_campaign/ledger.json'))
        if len(matches)!=1:raise RuntimeError('Ambiguous shielded ledger')
        ledger=matches[0]
    d=json.loads(ledger.read_text())
    boot=int(next(line.split()[1] for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime ')))
    started_at=boot+int(proc.identity[1])/os.sysconf('SC_CLK_TCK')
    if (campaign.process_identity(a.old_guard) or ())[:2]!=old[:2] or (campaign.process_identity(a.runner) or ())[:2]!=proc.identity[:2]:
        raise RuntimeError('Process identity changed before handoff')
    os.kill(a.old_guard,signal.SIGTERM)  # only supervisor; runner has its own session
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        now=campaign.process_identity(a.old_guard)
        if now is None or now[1]!=old[1] or now[2]=='Z':break
        time.sleep(.1)
    else:raise RuntimeError('Old guard did not exit')
    print(json.dumps({'event':'guard_adopted','runner_pid':a.runner,'old_guard_pid':a.old_guard,
                      'budget_seconds':campaign.current_budget(),'elapsed_seconds':time.time()-started_at,
                      'started_at_from_proc':started_at}),flush=True)
    campaign.monitor_sprint(proc,a.slug,a.sprint,d,started_at)

if __name__=='__main__':main()
