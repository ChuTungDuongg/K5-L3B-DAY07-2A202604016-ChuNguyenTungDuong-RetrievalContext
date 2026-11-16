import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from day6_agent import DenseRetriever, OpenAIController


class AdapterTests(unittest.TestCase):
    def test_maps_day6_results_and_forwards_filter(self):
        class Embedder:
            def embed_query(self, query):
                return [1.0]
        class Store:
            def search(self, strategy, vector, top_k, filters):
                self.args = strategy, vector, top_k, filters
                return [{'chunk_id': 'c1', 'document_id': 'd1', 'text': 'text',
                         'source': 'book', 'page': 1, 'metadata': {}, 'score': 0.9}]
        store = Store()
        result = DenseRetriever(Embedder(), store).search('q', filters={'section': '8.1'}, top_k=3)
        self.assertEqual(store.args, ('A', [1.0], 3, {'section': '8.1'}))
        self.assertEqual((result[0]['id'], result[0]['source_id']), ('c1', 'd1'))

    def test_controller_parses_model_action(self):
        class Responses:
            def create(self, **kwargs):
                return SimpleNamespace(output_text='{"action":"search","query":"database"}', usage=None)
        controller = OpenAIController(SimpleNamespace(responses=Responses()), 'model')
        self.assertEqual(controller.decide('question', [])['query'], 'database')

    def test_controller_reports_incomplete_api_response(self):
        class Responses:
            def create(self, **kwargs):
                return SimpleNamespace(status='incomplete', incomplete_details=SimpleNamespace(reason='max_output_tokens'),
                                       output_text='{', usage=None)
        controller = OpenAIController(SimpleNamespace(responses=Responses()), 'model')
        with self.assertRaisesRegex(RuntimeError, 'max_output_tokens'):
            controller.decide('question', [])

    def test_controller_allows_more_output_than_original_limit(self):
        class Responses:
            def create(self, **kwargs):
                assert kwargs['max_output_tokens'] > 600
                return SimpleNamespace(output_text='{"action":"search","query":"database"}', usage=None, status='completed')
        self.assertEqual(OpenAIController(SimpleNamespace(responses=Responses()), 'model').decide('q', [])['action'], 'search')

    def test_retries_incomplete_once_and_counts_both_calls(self):
        class Responses:
            def __init__(self): self.limits = []
            def create(self, **kwargs):
                self.limits.append(kwargs['max_output_tokens'])
                usage = SimpleNamespace(model_dump=lambda: {'input_tokens':1,'output_tokens':2})
                if len(self.limits) == 1:
                    return SimpleNamespace(status='incomplete', incomplete_details=SimpleNamespace(reason='max_output_tokens'), output_text='', usage=usage)
                return SimpleNamespace(status='completed', output_text='{"action":"search","query":"q"}', usage=usage)
        responses = Responses()
        controller = OpenAIController(SimpleNamespace(responses=responses), 'model')
        self.assertEqual(controller.decide('question', [])['action'], 'search')
        self.assertEqual(len(controller.usage), 2)
        self.assertGreater(responses.limits[1], responses.limits[0])

if __name__ == '__main__':
    unittest.main()
