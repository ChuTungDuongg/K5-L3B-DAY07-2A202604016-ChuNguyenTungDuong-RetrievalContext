import unittest
from starter.restore_day6 import validate_snapshot, verify_existing


class RestoreSnapshotTests(unittest.TestCase):
    def snapshot(self):
        return {'strategy':'A','dimensions':2,'chunks':[{'id':'c','source_id':'d','source':'s','page':1,'text':'t','metadata':{},'embedding':[0.1,0.2]}]}

    def test_invalid_dimension_rejected_before_database_write(self):
        data = self.snapshot()
        data['chunks'][0]['embedding'] = [0.1]
        with self.assertRaisesRegex(ValueError, 'dimension'):
            validate_snapshot(data)

    def test_existing_different_corpus_is_not_overwritten(self):
        data = self.snapshot()
        row = {**data['chunks'][0], 'text':'different'}
        with self.assertRaisesRegex(ValueError, 'different'):
            verify_existing([row], data['chunks'])

    def test_matching_index_can_be_reused(self):
        data = self.snapshot()
        validate_snapshot(data)
        verify_existing(data['chunks'], data['chunks'])


if __name__ == '__main__': unittest.main()
