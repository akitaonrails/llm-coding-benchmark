#!/usr/bin/env python3
"""Fixed synthetic SSE probes; preserve raw output and cache/latency evidence."""
import argparse,json,signal,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def cache_metrics(opts):
    req=urllib.request.Request(opts['baseURL'].removesuffix('/v1')+'/metrics',
        headers={'Authorization':'Bearer '+opts['apiKey']})
    try:
        with urllib.request.urlopen(req,timeout=15) as response:
            lines=response.read().decode().splitlines()
        return [line for line in lines if not line.startswith('#') and
                any(key in line for key in ('prefix_cache','spec_decode','num_requests_running'))]
    except Exception:
        return []

def main():
    ap=argparse.ArgumentParser();ap.add_argument('slug');ap.add_argument('--label',required=True)
    ap.add_argument('--prompt-records',type=int,default=160);a=ap.parse_args()
    def deadline(_signum,_frame):raise TimeoutError('Performance probe exceeded five-minute deadline')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(300)
    q=next(x for x in json.loads((ROOT/'config/b300_campaign.json').read_text())['queue'] if x['slug']==a.slug)
    opts=json.loads((ROOT/'config/opencode.benchmark.json').read_text())['provider']['runpod-vllm']['options']
    out=ROOT/'results-v4/_b300_campaign/migration-20261017'/f'perf-{a.slug}-{a.label}-{time.time_ns()}.json'
    records=[]
    prefix='\n'.join(f'Record {i:04}: item code {i*17:06}; inventory inspection requires counting units and recording discrepancies.' for i in range(a.prompt_records))
    for i in range(3):
        prompt=prefix+'\nExplain a systematic inventory reconciliation procedure in detail, with numbered steps. Keep writing until the output limit.'
        body={'model':q['served_name'],'messages':[{'role':'user','content':prompt}], 'max_tokens':256,'temperature':0,'stream':True,'stream_options':{'include_usage':True},'ignore_eos':True}
        req=urllib.request.Request(opts['baseURL']+'/chat/completions',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+opts['apiKey'],'Content-Type':'application/json'})
        before=cache_metrics(opts)
        t=time.monotonic();first=None;events=[];usage={}
        with urllib.request.urlopen(req,timeout=300) as response:
            for raw in response:
                line=raw.decode().strip()
                if not line.startswith('data: ') or line=='data: [DONE]':continue
                event=json.loads(line[6:]);events.append(event)
                if event.get('usage'):usage=event['usage']
                if any(any(c.get('delta',{}).get(k) for k in ('content','reasoning','reasoning_content','tool_calls')) for c in event.get('choices',[])) and first is None:first=time.monotonic()-t
        elapsed=time.monotonic()-t;tokens=usage.get('completion_tokens',0)
        r={'iteration':i,'elapsed_seconds':elapsed,'first_token_seconds':first,'usage':usage,'decode_tokens_per_second':(tokens-1)/(elapsed-first) if first is not None and tokens>1 else None,'events':events,'metrics_before':before,'metrics_after':cache_metrics(opts)};records.append(r)
        out.write_text(json.dumps({'slug':a.slug,'label':a.label,'request':body,'records':records},indent=2)+'\n')
        print(json.dumps({k:v for k,v in r.items() if k not in ('events','metrics_before','metrics_after')}),flush=True)
    print('Evidence: '+str(out))
if __name__=='__main__':main()
