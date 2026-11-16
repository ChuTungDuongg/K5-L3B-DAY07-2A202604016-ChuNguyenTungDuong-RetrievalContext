import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_test import evaluate_case


class TestRunnerTests(unittest.TestCase):
    def test_agent_sees_question_not_gold_and_result_has_metrics(self):
        chunk = {'id':'c1','source_id':'d','source':'s','page':1,'text':'evidence', 'metadata':{},'score':0.9}
        class Retriever:
            def search(self, query, *, filters, top_k):
                self.query = query
                return [chunk]
        r = Retriever()
        case = {'id':'t1','question':'query','split':'test','answerable':True}
        gold = [{'source_id':'d','page':1,'evidence':'evidence'}]
        def fake_agent(question, controller, retriever, **kwargs):
            self.assertEqual(question, 'query')
            self.assertNotIn('gold', kwargs)
            return {'status':'answered','answer':'x [c1]','citations':['c1'],
                    'events':[{'event':'search','context_ids':['c1'],'results':[chunk]}]}
        with patch('run_test.run_agent', fake_agent):
            result = evaluate_case(case, gold, r, object(), budget=2000, max_searches=3)
        self.assertEqual(r.query, 'query')
        self.assertTrue(result['retrieval_original']['hit1'])
        self.assertTrue(result['agent_context_hit'])

    def test_unanswerable_not_in_retrieval_denominator(self):
        class Retriever:
            def search(self, query, *, filters, top_k): return []
        case = {'id':'t2','question':'query','split':'test','answerable':False}
        fake = {'status':'abstain','answer':'no evidence','citations':[],'events':[]}
        with patch('run_test.run_agent', return_value=fake):
            result = evaluate_case(case, None, Retriever(), object(), budget=2000, max_searches=3)
        self.assertIsNone(result['retrieval_original']['hit1'])
        self.assertIsNone(result['agent_context_hit'])

if __name__ == '__main__': unittest.main()
