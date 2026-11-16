"""Round isolation and provenance checks using local synthetic artifacts only."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from advanced import analyze, official_test, run, select, verify
from advanced.budget import save
from advanced.source import digest


class AdvancedRoundTests(unittest.TestCase):
    def test_round_paths_keep_legacy_runs_and_benchmarks_separate(self):
        self.assertTrue(hasattr(run, 'round_results'), 'Round-aware paths are missing')
        root = Path('workspace')
        self.assertEqual(run.round_results(1, root), root/'advanced/results')
        self.assertEqual(run.round_results(2, root), root/'advanced/results/round2')
        self.assertEqual(run.benchmark_directory(2, root), root/'advanced/benchmark/round2')
        self.assertEqual(run.case_path({'split': 'test'}, root), root/'advanced/benchmark/test.json')
        self.assertEqual(run.case_path({'split': 'dev', 'round': 2,
                                      'benchmark_path': 'advanced/benchmark/round2/dev.json'}, root),
                         root/'advanced/benchmark/round2/dev.json')
        with self.assertRaises(ValueError):
            run.case_path({'split': 'test', 'round': 2,
                           'benchmark_path': 'advanced/benchmark/test.json'}, root)

    def test_round_two_config_adds_review_without_mutating_legacy_config(self):
        self.assertTrue(hasattr(run, 'configs_for_round'), 'Round-aware configs are missing')
        current = run.configs_for_round(2)
        self.assertTrue(current['baseline']['review_before_answer'])
        self.assertEqual(current['candidate']['citation_policy'], 'full_page_specific_locator')
        current['baseline']['max_steps'] = 99
        self.assertEqual(run.configs_for_round(2)['baseline']['max_steps'], 3)
        self.assertNotIn('review_before_answer', run.configs_for_round(1)['baseline'])

    def test_analysis_uses_each_round_benchmark_and_preserves_old_derived_files(self):
        self.assertTrue(hasattr(analyze, 'build_ledger'), 'Version-aware analysis is missing')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events = root/'advanced/results/api-events'
            requests = []
            for number, run_id in [(1, 'legacy-dev'), (2, 'round2-dev')]:
                benchmark = root/'advanced/benchmark'/('round2' if number == 2 else '')/'dev.json'
                save(benchmark, [{'id': 'q'+str(number), 'group': 'text'}])
                directory = root/'advanced/results'/('round2' if number == 2 else '')/'runs'/run_id
                cfg = {'run_id': run_id, 'round': number, 'split': 'dev', 'config_name': 'baseline',
                       'config': {}, 'started_local': '2026-11-16T12:00:00',
                       'benchmark_sha256': digest(benchmark)}
                if number == 2:
                    cfg['benchmark_path'] = 'advanced/benchmark/round2/dev.json'
                save(directory/'config.json', cfg)
                save(directory/'traces.json', [{'query_id': 'q'+str(number), 'status': 'answered',
                                               'elapsed_ms': 10, 'events': []}])
                save(directory/'reviews-proposed.json', [{'query_id': 'q'+str(number),
                                                          'passed': True, 'reason': 'synthetic check'}])
                save(directory/'summary.json', {})
                if number == 1:
                    save(directory/'metrics.json', {'historical': 'do not rewrite'})
                usage = {'input_tokens': 1000, 'output_tokens': 100}
                save(events/(str(number)+'.json'), {'id': str(number), 'label': run_id+':q:step0',
                                                  'usage': usage, 'elapsed_seconds': 1})
                requests.append({'id': str(number), 'reserved_usd': '0.001', 'estimated_usd': '0.00015'})
            old_metrics = root/'advanced/results/runs/legacy-dev/metrics.json'
            before = old_metrics.read_bytes()
            save(root/'advanced/results/budget.json', {'cap_usd': '5', 'requests': requests})
            ledger = analyze.build_ledger(2, root=root)
            self.assertEqual({r['round'] for r in ledger['runs']}, {1, 2})
            self.assertEqual([r['metrics']['passed'] for r in ledger['runs']], [1, 1])
            self.assertEqual(ledger['total']['estimated_usd'], '0.0003000000')
            self.assertEqual(old_metrics.read_bytes(), before)
            self.assertTrue((root/'advanced/results/round2/runs/round2-dev/metrics.json').exists())

    def test_official_claim_is_separate_per_round_and_never_overwrites(self):
        self.assertTrue(hasattr(official_test, 'claim_official'), 'Per-round atomic marker is missing')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save(root/'advanced/results/selection-freeze.json', {'round': 1})
            save(root/'advanced/results/round2/selection-freeze.json', {'round': 2})
            old, _ = official_test.claim_official(1, root=root)
            old_bytes = old.read_bytes()
            new, claim = official_test.claim_official(2, root=root)
            self.assertNotEqual(old, new)
            self.assertEqual(claim['round'], 2)
            with self.assertRaises(FileExistsError):
                official_test.claim_official(2, root=root)
            self.assertEqual(old.read_bytes(), old_bytes)

    def test_selector_rejects_a_second_current_dev_attempt(self):
        self.assertTrue(hasattr(select, 'eligible_dev_pair'), 'Round-aware Dev selection is missing')
        rows = [{'round': 1, 'split': 'test', 'config_name': 'baseline', 'pipeline_sha256': {'a': 'x'}},
                {'round': 2, 'split': 'dev', 'config_name': 'baseline', 'pipeline_sha256': {'a': 'x'}},
                {'round': 2, 'split': 'dev', 'config_name': 'candidate', 'pipeline_sha256': {'a': 'x'}}]
        pair = select.eligible_dev_pair(rows, 2, {'a': 'x'})
        self.assertEqual(len(pair), 2)
        with self.assertRaises(ValueError):
            select.eligible_dev_pair(rows+[dict(rows[-1])], 2, {'a': 'x'})
        with self.assertRaises(ValueError):
            select.eligible_dev_pair(rows+[{'round': 2, 'split': 'test'}], 2, {'a': 'x'})

    def test_historical_pipeline_verification_resolves_archived_bytes(self):
        self.assertTrue(hasattr(verify, 'verify_historical_hashes'), 'Archived pipeline validation is missing')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            live = root/'advanced/agent.py'
            live.parent.mkdir(parents=True)
            live.write_text('new runtime', encoding='utf-8')
            archived = root/'advanced/history/round1-selected/advanced/agent.py'
            archived.parent.mkdir(parents=True)
            archived.write_text('selected runtime', encoding='utf-8')
            expected = digest(archived)
            verify.verify_historical_hashes({'advanced/agent.py': expected}, root=root)
            archived.write_text('corrupted runtime', encoding='utf-8')
            with self.assertRaises(ValueError):
                verify.verify_historical_hashes({'advanced/agent.py': expected}, root=root)


if __name__ == '__main__':
    unittest.main()
