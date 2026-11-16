import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_dev import fuse, evaluate_result

class DevRunnerTests(unittest.TestCase):
    def test_rrf_combines_shared_result(self):
        a, b = {'id':'a'}, {'id':'b'}
        fused = fuse([a, b], [b, a], 2)
        self.assertEqual({x['id'] for x in fused}, {'a', 'b'})
        self.assertEqual(fused[0]['ranks'], {'dense': 1, 'tfidf': 2})

    def test_evaluation_reports_retrieval_and_context_separately(self):
        rows = [{'id':'1','source_id':'d','page':1,'text':'other'},
                {'id':'2','source_id':'d','page':1,'text':'evidence'}]
        out = evaluate_result(rows, ['1'], [{'source_id':'d','page':1,'evidence':'evidence'}])
        self.assertEqual(out, {'hit1':False, 'hit3':True, 'context_hit':False})

if __name__ == '__main__': unittest.main()
