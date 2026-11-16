import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class StarterImplementationTests(unittest.TestCase):
    def test_starter_controller_is_concrete_and_compatibility_alias_is_same(self):
        from starter.agentic import Controller
        from day6_agent import OpenAIController
        response = SimpleNamespace(output_text='{"action":"search","query":"database"}', usage=None, status='completed')
        client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: response))
        self.assertEqual(Controller(client, 'model').decide('q', [])['query'], 'database')
        self.assertIs(Controller, OpenAIController)

    def test_starter_retriever_is_concrete_and_normalizes_day6_ids(self):
        from starter.agentic import Retriever
        embedder = SimpleNamespace(embed_query=lambda query: [1.0])
        row = {'chunk_id':'c','document_id':'d','source':'book','page':1,'text':'evidence','metadata':{},'score':0.9}
        store = SimpleNamespace(search=lambda *args, **kwargs: [row])
        result = Retriever(embedder, store).search('q', filters=None, top_k=3)
        self.assertEqual((result[0]['id'], result[0]['source_id']), ('c', 'd'))


if __name__ == '__main__':
    unittest.main()
