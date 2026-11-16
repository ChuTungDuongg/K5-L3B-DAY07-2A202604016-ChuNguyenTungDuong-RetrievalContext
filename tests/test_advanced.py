import json
import tempfile
import unittest
from pathlib import Path

from advanced.budget import Budget, BudgetExceeded
from advanced.metrics import summarize
from advanced.source import clean_text, split_text
from advanced.agent import validate_answer, calculate


class AdvancedTests(unittest.TestCase):
    def test_budget_refuses_next_request_and_keeps_unknown_reserve(self):
        with tempfile.TemporaryDirectory() as folder:
            b = Budget(Path(folder)/'budget.json', cap='0.01')
            reservation = b.reserve('case', '0.006')
            b.finish(reservation, None, error='timeout')
            with self.assertRaises(BudgetExceeded):
                b.reserve('next', '0.005')
            self.assertEqual(b.snapshot()['unknown_reserved_usd'], '0.006')

    def test_recorded_usage_releases_only_the_appropriate_reservation(self):
        with tempfile.TemporaryDirectory() as folder:
            b = Budget(Path(folder)/'budget.json', cap='1')
            ticket = b.reserve('case', '0.1')
            b.finish(ticket, {'input_tokens':1000,'output_tokens':100})
            self.assertEqual(b.snapshot()['recorded_estimated_usd'], '0.00015')
            self.assertEqual(b.snapshot()['unknown_reserved_usd'], '0')

    def test_errors_and_unreviewed_cases_stay_in_strict_denominator(self):
        cases=[{'id':'a','group':'table'}, {'id':'b','group':'chart'}, {'id':'c','group':'text'}]
        traces=[{'query_id':'a','status':'answered'}, {'query_id':'b','status':'error'}]
        labels=[{'query_id':'a','passed':True,'reason':'source checked'}]
        m=summarize(cases,traces,labels)
        self.assertEqual((m['passed'],m['total'],m['errors'],m['missing_results']), (1,3,1,1))
        self.assertFalse(m['threshold_met'])

    def test_source_cleanup_and_chunks_preserve_every_character(self):
        s=clean_text('infor\u00admation\r\n data\x00')
        self.assertEqual(s, 'information\n data')
        original='word '*300
        chunks=split_text(original, size=350, overlap=50)
        self.assertTrue(all(len(c['text']) <= 350 for c in chunks))
        recovered=chunks[0]['text']+''.join(c['text'][50:] for c in chunks[1:])
        self.assertEqual(recovered, original)

    def test_citations_cannot_point_to_unseen_pages_or_invalid_regions(self):
        action={'status':'answered','answer':'A claim', 'citations':[{'page':10,'region_label':'Figure 1.1','bbox':[0,0,1,1],'quote':'claim'}]}
        with self.assertRaises(ValueError):
            validate_answer(action, {9})
        action['citations'][0]['page']=9
        action['citations'][0]['bbox']=[0.8,0,0.1,1]
        with self.assertRaises(ValueError):
            validate_answer(action, {9})

    def test_calculator_handles_decimal_units_without_executing_code(self):
        self.assertEqual(calculate('(89 - 60) / 60 * 100'), '48.33333333333333333333333333')
        self.assertEqual(calculate('12 ÷ 3 × 2'), '8')
        with self.assertRaises(ValueError):
            calculate("__import__('os').getcwd()")

    def test_verification_rechecks_answer_and_preserves_original_region(self):
        from unittest.mock import patch
        from advanced.agent import Agent
        from pathlib import Path
        action={'action':'answer','expression':'','queries':[],'pages':[],'status':'answered',
                'answer':'The value is 2.', 'citations':[{'page':10,'region_label':'Table 1','bbox':[.2,.2,.4,.4],'quote':'2'}]}
        corrected={**action,'answer':'The value is 3.'}
        class Retriever:
            def search(self,*args,**kwargs):
                return [{'page':10,'score':1,'ranks':{},'labels':['Table 1'],'printed_page':'1','text':'3','regions':[]}]
        class API:
            def __init__(self): self.calls=[]
            def call(self,label,*args,**kwargs):
                self.calls.append(label)
                return (action if len(self.calls)==1 else corrected),{'id':str(len(self.calls))}
        api=API()
        with patch('advanced.agent.render_page',return_value=Path('page.jpg')):
            result=Agent(Retriever(),api,{'image_pages':1,'max_images':1,'max_steps':2,
                                        'review_before_answer':True,'citation_policy':'full_page_specific_locator'}).run('Question','case')
        self.assertEqual(result['answer'],'The value is 3.')
        self.assertEqual(result['citations'][0]['bbox'],[0,0,1,1])
        self.assertEqual(result['citations'][0]['model_bbox'],[.2,.2,.4,.4])
        self.assertEqual(len(api.calls),2)

    def test_proposed_labels_do_not_claim_confirmed_threshold(self):
        m=summarize([{'id':'a','group':'table'}],[{'query_id':'a','status':'answered'}],
                    [{'query_id':'a','passed':True,'reason':'source checked'}])
        self.assertTrue(m['score_threshold_met'])
        self.assertFalse(m['threshold_met'])

    def test_underestimated_reservation_latches_off_future_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            b=Budget(Path(folder)/'budget.json',cap='1')
            ticket=b.reserve('too_small','0.00001')
            with self.assertRaises(BudgetExceeded):
                b.finish(ticket,{'input_tokens':1000,'output_tokens':100})
            with self.assertRaises(BudgetExceeded):
                b.reserve('must_stop','0.001')

    def test_test_run_refuses_changed_benchmark_freeze(self):
        from advanced.run import verify_selection
        selection={'config_name':'baseline','config':{'max_steps':3},
                   'pipeline_sha256':{'agent.py':'a'},'benchmark_freeze_sha256':'original'}
        with self.assertRaises(ValueError):
            verify_selection(selection,'baseline',{'max_steps':3},{'agent.py':'a'},'modified')
        verify_selection(selection,'baseline',{'max_steps':3},{'agent.py':'a'},'original')


if __name__ == '__main__': unittest.main()
