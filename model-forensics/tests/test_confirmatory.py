import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'confirmatory'))
import experiment as e
import analysis as a
import panel


def row(probe,profile,text='a',status='ok',rep=0):
    return dict(request=dict(probe=probe,profile=profile,replicate=rep),text=text,status=status)


class ConfirmatoryTests(unittest.TestCase):
    def test_panels_unique_deterministic_and_disjoint(self):
        ts=panel.tokens()
        self.assertEqual(len(ts),1024)
        self.assertEqual(len({p['prompt'] for p in ts}),1024)
        self.assertEqual(ts,panel.tokens())
        self.assertEqual(sum(p['split']=='holdout' for p in ts),768)
        ds,hs,ps=panel.behavioral()
        self.assertEqual(len(ds),48);self.assertEqual(len(ps),48)
        self.assertFalse({p['prompt'] for p in ds}&{p['prompt'] for bank in hs.values() for p in bank})
        for n in [1,7,49,12345]:self.assertEqual(int(panel.base7(n),7),n)

    def test_selection_rejects_genesys_and_requires_repeated_distinctive_error(self):
        probe={'id':'d','family':'count','expected':'4'}
        rows=[row('d','gpt4o-a','5') for _ in range(3)]
        rows += [row('d',label,'4') for label in ['qwen','llama'] for _ in range(3)]
        self.assertEqual(e.choose(rows,[probe])['families'],['count'])
        with self.assertRaisesRegex(ValueError,'only reference'):
            e.choose(rows+[row('d','genesys','5')],[probe])
        rows += [row('d',label,'5') for label in ['qwen','llama'] for _ in range(4)]
        self.assertEqual(e.choose(rows,[probe])['families'],[])

    def test_gate_requires_known_controls_to_separate(self):
        def c(lo,hi):return {'adequate':True,'distance':{'interval95':[lo,hi]}}
        positives=['gpt4o-b','gpt4o-system','gpt4o-verify','gpt4o-snapshot']
        controls={p:c(.1,.2) for p in positives}
        controls.update({p:c(.5,.7) for p in ['qwen','qwen-verify','llama']})
        self.assertAlmostEqual(a.gate(controls)['threshold'],.35)
        controls['gpt4o-verify']=c(.1,.6)
        self.assertIsNone(a.gate(controls)['threshold'])
        controls['gpt4o-verify']['adequate']=False
        self.assertEqual(a.gate(controls)['decision'],'inconclusive_insufficient_control_coverage')

    def test_identical_disjoint_and_missing_distributions(self):
        probes=[dict(id=f'p{i}',block=f'b{i}',kind='exact',expected='a') for i in range(10)]
        base=[row(p['id'],'gpt4o-a','a',rep=r) for p in probes for r in range(6)]
        same=[row(p['id'],'genesys','a',rep=r) for p in probes for r in range(6)]
        other=[row(p['id'],'genesys','b',rep=r) for p in probes for r in range(6)]
        self.assertEqual(a.compare(probes,base,same,'genesys')['distance']['mean'],0)
        self.assertEqual(a.compare(probes,base,other,'genesys')['distance']['mean'],1)
        self.assertFalse(a.compare(probes,base,same[:12],'genesys')['adequate'])
        calibration={'threshold':.3,'decision':'calibrated_separation'}
        self.assertEqual(a.target(probes,base,same,calibration)['conclusion'],'consistent_with_tested_gpt4o_control_envelope')
        self.assertEqual(a.target(probes,base,other,calibration)['conclusion'],'inconsistent_with_tested_gpt4o_control_envelope')
        self.assertEqual(a.target(probes,base,other,{'threshold':None,'decision':'inconclusive_controls_overlap'})['conclusion'],'inconclusive')

    def test_tokenizer_offset_frozen_on_calibration_partition(self):
        probes=[{'id':'a','family':'x','split':'offset'},{'id':'b','family':'x','split':'holdout'}]
        m={'tokens':probes,'encodings':{'o200k_base':{'counts':{'a':3,'b':7}}}}
        rows=[]
        for profile in ['genesys','gpt4o-a']:
            for p,count in [('a',103),('b',108)]:rows.append({**row(p,profile),'usage':{'prompt_tokens':count}})
        result=a.tokenizer(m,rows)['profiles']['genesys']['o200k_base']
        self.assertEqual(result['offset'],100)
        self.assertEqual(result['exact_matches'],0)

    def test_wrapper_calls_and_interrupted_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for sub in ['records','started','calls']:(p/sub).mkdir()
            task={'id':'000000','probe':'p','profile':'gpt4o-verify'}
            probe={'prompt':'Return a','kind':'exact'}
            profile=next(x for x in e.configs() if x['label']=='gpt4o-verify')
            settings=dict(endpoint_concurrency=1,min_interval_seconds=0,rate_cooldown_seconds=0)
            responses=[{'status':'ok','text':'b'},{'status':'ok','text':'a'}]
            with patch.object(e,'http_call',side_effect=responses) as call:
                result=e.observation(task,probe,profile,{'max_tokens':512,'timeout_seconds':1},p,e.Limiter(settings),[])
                self.assertEqual(result['text'],'a');self.assertEqual(call.call_count,2)
                self.assertEqual(len(result['calls']),2)
            # A journaled but unfinished observation is uncertain, never sent again.
            task={**task,'id':'000001'};e.atomic(p/'started/000001.json',e.seal({'request':task}))
            with patch.object(e,'http_call') as call:
                result=e.observation(task,probe,profile,{'max_tokens':512,'timeout_seconds':1},p,e.Limiter(settings),[])
                self.assertEqual(result['status'],'interrupted_unknown');call.assert_not_called()

    def test_sealed_record_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'record.json';e.atomic(p,e.seal({'status':'ok'}))
            d=json.loads(p.read_text());d['status']='changed';p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'Integrity'):e.read_sealed(p)

    def test_circuit_breaker_and_no_second_call_on_failure(self):
        limiter=e.Limiter(dict(endpoint_concurrency=1,min_interval_seconds=0,rate_cooldown_seconds=0))
        for _ in range(3):limiter.finish({'status':'invalid_response'})
        self.assertFalse(limiter.reserve())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for sub in ['records','started','calls']:(p/sub).mkdir()
            with patch.object(e,'http_call',return_value={'status':'http_error','http_status':429}) as call:
                profile=next(x for x in e.configs() if x['label']=='gpt4o-verify')
                settings=dict(endpoint_concurrency=1,min_interval_seconds=0,rate_cooldown_seconds=0)
                result=e.observation({'id':'0'}, {'prompt':'a','kind':'exact'},profile,{'max_tokens':10,'timeout_seconds':1},p,e.Limiter(settings),[])
                self.assertEqual(call.call_count,1);self.assertEqual(result['status'],'http_error')

    def test_invalid_choices_excluded_and_perturbation_sensitivity(self):
        ps=[dict(id=f'p{v}',block='b',kind='choice',variant=v,options=['a','b']) for v in [0,1]]
        refs=[row(p['id'],'gpt4o-a','a' if p['variant']==0 else 'b') for p in ps for _ in range(6)]
        candidates=[row(p['id'],'genesys','a') for p in ps for _ in range(6)]
        self.assertEqual(a.perturbation(ps,refs,candidates,'genesys',4)['mean'],1)
        self.assertEqual(a.distribution([row('p0','genesys','unlisted')]*6,ps[0],'genesys')[0],{})
