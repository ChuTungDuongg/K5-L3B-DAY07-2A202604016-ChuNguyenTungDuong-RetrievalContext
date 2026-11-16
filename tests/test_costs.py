import unittest
from decimal import Decimal
from scripts.summarize_results import estimate_usage


class CostTests(unittest.TestCase):
    def test_cached_input_is_not_charged_again_as_uncached(self):
        result = estimate_usage({'input_tokens':1000,'input_tokens_details':{'cached_tokens':200},'output_tokens':100})
        self.assertEqual(result['uncached_input_tokens'], 800)
        self.assertEqual(Decimal(result['estimated_usd']), Decimal('0.000132'))

    def test_missing_usage_does_not_invent_tokens(self):
        self.assertEqual(estimate_usage({'input_tokens':0,'output_tokens':0})['estimated_usd'], '0.0000000000')


if __name__ == '__main__': unittest.main()
