import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'confirmatory'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'oss'))
import experiment as e
import oss_analysis as a
import oss_probes
import client


def fixtures(n=8,reps=6):
    ps=[dict(id=str(i),block=str(i),family='arithmetic',kind='exact',expected='1') for i in range(n)]
    rows=[dict(request=dict(probe=p['id'],profile=k),status='ok',text='2' if k in ['oss120']+a.POSITIVES else '1')
          for p in ps for k in ['oss120','oss20']+a.POSITIVES+a.NEGATIVES for _ in range(reps)]
    return ps,rows


class OssTests(unittest.TestCase):
    def test_probes_deterministic_and_unique(self):
        ps=oss_probes.build();self.assertEqual(ps,oss_probes.build());self.assertEqual(len(ps),48)
        self.assertEqual(len({p['id'] for p in ps}),48)
        self.assertEqual(len({p['block'] for p in ps}),38)

    def test_selection_and_block_deduplication(self):
        ps,rs=fixtures();s=a.select(ps,rs);self.assertEqual(s['decision'],'validate')
        ps[1]['block']=ps[0]['block'];self.assertEqual(a.select(ps,rs)['decision'],'stop_insufficient_distinctive_signatures')

    def test_target_data_forbidden_in_both_gates(self):
        ps,rs=fixtures();rs.append(dict(request=dict(profile='genesys')))
        for f in [a.select,a.validate]:
            with self.assertRaises(ValueError):f(ps,rs)

    def test_fresh_validation_can_reject_discovery_signature(self):
        ps,discovery=fixtures();self.assertEqual(a.select(ps,discovery)['decision'],'validate')
        ps,validation=fixtures()
        for r in validation:r['text']='1'
        self.assertEqual(a.validate(ps,validation)['decision'],'stop_controls_overlap')

    def test_gate_and_target_decisions(self):
        ps,rs=fixtures();gate=a.validate(ps,rs);self.assertEqual(gate['decision'],'pass')
        target=[dict(request=dict(probe=p['id'],profile='genesys'),status='ok',text='2') for p in ps for _ in range(8)]
        result=a.target(ps,rs,target,gate);self.assertEqual(result['decision'],'matches_tested_oss120_behavioral_envelope')
        self.assertEqual(result['comparison']['details'][0]['same_wrong_answer'],1)
        for r in target:r['text']='1'
        self.assertEqual(a.target(ps,rs,target,gate)['decision'],'outside_tested_oss120_behavioral_envelope')
        self.assertEqual(a.target(ps,rs,target,{'decision':'stop'})['decision'],'inconclusive')

    def test_truncation_is_missing_not_wrong(self):
        ps,rs=fixtures()
        for r in rs:
            if r['request']['profile']=='kimi':r['status']='truncated'
        self.assertEqual(a.validate(ps,rs)['decision'],'stop_insufficient_coverage')

    def test_normalization_only_format(self):
        self.assertEqual(a.normalize('```json\n"你好"\n```'),'你好')
        self.assertEqual(a.normalize('Answer: 42'),'Answer: 42')
        self.assertNotEqual(a.normalize('AÇÃO'),a.normalize('ação'))

    def test_routing_and_metadata(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):return json.dumps(dict(provider='Groq',model='openai/gpt-oss-120b',choices=[dict(message={'content':'A'},finish_reason='stop')],usage={'completion_tokens':2})).encode()
        class Opener:
            def open(self,request,timeout):
                body=json.loads(request.data);assert body['provider']['allow_fallbacks'] is False
                assert body['provider']['order']==['groq'];assert 'temperature' not in body
                return Response()
        p=dict(model='openai/gpt-oss-120b',base_url='https://example.test',key_env='TEST_FORENSIC_KEY',parameters={'provider':{'order':['groq'],'allow_fallbacks':False}})
        with patch.dict('os.environ',TEST_FORENSIC_KEY='local-placeholder'),patch('urllib.request.build_opener',return_value=Opener()):
            r=client.call(p,[],4096,120,['local-placeholder'])
        self.assertEqual(r['provider'],'Groq');self.assertEqual(r['status'],'ok')
        self.assertNotIn('local-placeholder',json.dumps(r))
