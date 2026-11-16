"""Offline protocol tests; never counted as bonus model quality."""
import unittest
import json
import io
from unittest.mock import patch
from src.advanced.agent import calculate, valid_citations
from src.advanced.benchmark import score
from src.advanced.agent import run
from src.advanced.common import reserve_budget
from src.advanced.citation_alignment import align


class AdvancedTests(unittest.TestCase):
    def test_calculator_rejects_code_and_supports_percent_arithmetic(self):
        self.assertAlmostEqual(calculate('(100000*2*0.5-25000)/25000'),3)
        self.assertAlmostEqual(calculate('44.04-17.4'),26.64)
        for text in ["__import__('os').system('whoami')",'2**10000','True+1','sum([1,2])']:
            with self.assertRaises(ValueError): calculate(text)

    def test_unopened_or_invalid_region_is_rejected(self):
        c={'page':17,'bbox':[0.1,0.2,0.9,0.8],'label':'Infographic','support':'Comparison'}
        self.assertTrue(valid_citations([c],[17]))
        self.assertFalse(valid_citations([c],[12]))
        self.assertFalse(valid_citations([{**c,'bbox':[0,0,2,1]}],[17]))

    def test_bonus_counts_errors_in_denominator(self):
        cases=[{'id':'x','group':'text','answerable':True,'required_pages':[1]},
               {'id':'y','group':'unanswerable','answerable':False,'required_pages':[]}]
        traces=[{'query_id':'x','status':'error','usage':[],'elapsed_ms':5},
                {'query_id':'y','status':'abstain','usage':[],'elapsed_ms':5}]
        reviews=[{'query_id':'y','passed':True,'reason':'No reported evidence.',
                  'original_page_verified':True}]
        result=score(cases,traces,reviews)
        self.assertEqual((result['passed'],result['total']),(1,2))
        self.assertFalse(result['threshold_met'])
        self.assertEqual(result['system_errors'],1)

    def test_negative_can_explicitly_state_missing_evidence_without_guessing(self):
        cases=[{'id':'x','group':'unanswerable','answerable':False,'required_pages':[]}]
        traces=[{'query_id':'x','status':'answered','answer':'The manufacturer is not named.',
                 'usage':[],'elapsed_ms':1}]
        review={'query_id':'x','passed':True,'reason':'Original image has no brand label.',
                'original_page_verified':True,'explicit_insufficient_evidence':True}
        self.assertEqual(score(cases,traces,[review])['passed'],1)
        review['explicit_insufficient_evidence']=False
        with self.assertRaises(ValueError):score(cases,traces,[review])

    def test_multihop_needs_all_evidence_pages(self):
        cases=[{'id':'x','group':'multi_hop','answerable':True,'required_pages':[1,2]}]
        traces=[{'query_id':'x','status':'answered','citations':[{'page':1}],
                 'usage':[],'elapsed_ms':10}]
        reviews=[{'query_id':'x','passed':True,'reason':'Candidate label',
                  'original_page_verified':True,'citations_support_all_claims':True}]
        with self.assertRaises(ValueError): score(cases,traces,reviews)

    def test_multiple_readonly_inspections_are_merged(self):
        def call(name,args):
            return {'function':{'name':name,'arguments':json.dumps(args)}}
        responses=[({'tool_calls':[call('search',{'query':'reporting'})]},{}),
                   ({'tool_calls':[call('inspect_pages',{'pages':[31]}),call('inspect_pages',{'pages':[32]})]},{}),
                   ({'tool_calls':[call('finish',{'status':'answered','answer':'Supported test answer',
                     'citations':[{'page':32,'bbox':[.1,.1,.9,.4],'label':'Table 1','support':'Test only'}]})]}, {})]
        class Fake:
            def search(self,query,top_k):return []
            def page_regions(self,pages):return []
        config={'model':'offline-test','top_k':3,'max_searches':2,'max_pages':4,'max_turns':4}
        with patch('src.advanced.agent.complete',side_effect=responses),patch('src.advanced.agent.image_part',return_value={'type':'text','text':'offline image placeholder'}):
            t=run('q',Fake(),config)
        self.assertEqual(t['status'],'answered')
        self.assertEqual(t['opened_pages'],[31,32])

    def test_budget_guard_blocks_before_paid_request(self):
        payload={'data':{'limit':.7,'limit_remaining':.003,'usage_daily':.697}}
        with patch('src.advanced.common.urllib.request.urlopen',return_value=io.BytesIO(json.dumps(payload).encode())),patch('src.advanced.common._inflight',0):
            with self.assertRaisesRegex(RuntimeError,'Budget guard'):
                reserve_budget('offline-test-key','google/gemini-2.5-flash-lite')

    def test_mixed_search_inspect_batch_is_read_before_answer(self):
        def call(name,args):return {'function':{'name':name,'arguments':json.dumps(args)}}
        responses=[({'tool_calls':[call('search',{'query':'table'}),call('inspect_pages',{'pages':[32]})]},{}),
            ({'tool_calls':[call('finish',{'status':'answered','answer':'Test evidence',
                'citations':[{'page':32,'bbox':[.1,.1,.9,.4],'label':'Table 1','support':'Test'}]})]}, {})]
        class Fake:
            def search(self,query,top_k):return []
            def page_regions(self,pages):return []
        with patch('src.advanced.agent.complete',side_effect=responses),patch('src.advanced.agent.image_part',return_value={'type':'text','text':'offline image'}):
            t=run('q',Fake(),{'model':'offline','top_k':3,'max_searches':2,'max_pages':4,'max_turns':4})
        self.assertEqual(t['status'],'answered')
        self.assertEqual([e['image_pages'] for e in t['events'] if e['event']=='model'],[[],[32]])

    def test_uninspected_citation_can_be_repaired(self):
        def call(name,args):return {'tool_calls':[{'function':{'name':name,'arguments':json.dumps(args)}}]},{}
        answer={'status':'answered','answer':'Test evidence','citations':[{'page':32,'bbox':[.1,.1,.9,.4],'label':'Table 1','support':'Test'}]}
        responses=[call('search',{'query':'table'}),call('finish',answer),call('inspect_pages',{'pages':[32]}),call('finish',answer)]
        class Fake:
            def search(self,query,top_k):return []
            def page_regions(self,pages):return []
        with patch('src.advanced.agent.complete',side_effect=responses),patch('src.advanced.agent.image_part',return_value={'type':'text','text':'offline image'}):
            t=run('q',Fake(),{'model':'offline','top_k':3,'max_searches':2,'max_pages':4,'max_turns':5})
        self.assertEqual(t['status'],'answered')
        self.assertTrue(any(e['event']=='validation_feedback' for e in t['events']))

    def test_document_catalog_aligns_selected_label_without_gold(self):
        citation={'page':12,'bbox':[.8,.8,.9,.9],'label':'Figure 6','support':'Diagram claim'}
        rows=[{'id':'adv:p012:v00','page':12,'metadata':{'label':'Figure 6 — Process','bbox':[.1,.2,.9,.7]}}]
        result=align(citation,rows,None)
        self.assertEqual(result['bbox'],[.1,.2,.9,.7])
        self.assertEqual(result['model_bbox'],[.8,.8,.9,.9])
        self.assertEqual(result['region_id'],'adv:p012:v00')


if __name__=='__main__': unittest.main()
