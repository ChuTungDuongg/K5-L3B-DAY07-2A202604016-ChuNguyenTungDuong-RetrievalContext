import hashlib
import unittest

from scripts.summarize_results import ROOT, dataset_version


class DatasetVersionTests(unittest.TestCase):
    def test_partial_final_dev_run_uses_dataset_hash_not_selected_ids(self):
        path = ROOT / 'starter/data/day6-A/questions-dev.json'
        config = {'data_sha256': {'questions-dev.json': hashlib.sha256(path.read_bytes()).hexdigest()}}
        self.assertEqual(dataset_version('dev', config, [{'query_id': 'dev01'}]), 'dev-final')

    def test_new_run_records_version_even_when_only_one_case_is_run(self):
        self.assertEqual(dataset_version('dev', {'dataset_version': 'dev-final'},
                                         [{'query_id': 'dev01'}]), 'dev-final')

    def test_unversioned_partial_run_is_not_assumed_to_be_original(self):
        self.assertEqual(dataset_version('dev', {}, [{'query_id': 'dev01'}]), 'dev-unversioned')


if __name__ == '__main__':
    unittest.main()
