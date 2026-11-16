"""Verify round-specific provenance and historical runtime bytes without model calls."""
import argparse
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .analyze import read, usage_total
from .budget import save
from .metrics import summarize
from .run import fingerprints, round_results, benchmark_directory, case_path
from .source import DATA, ROOT, digest


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify_historical_hashes(hashes, *, root=None):
    root = Path(ROOT if root is None else root)
    for name, expected in hashes.items():
        candidates = [root/'advanced/history/round1-selected'/name,
                      root/'advanced/history/pipeline-v1'/name]
        archived = [p for p in candidates if p.exists()]
        paths = archived if archived else [root/name]
        check(any(p.exists() and digest(p) == expected for p in paths),
              'Historical runtime/data checksum changed: '+name)


def verify_round(number, rows, *, root=None):
    root = Path(ROOT if root is None else root)
    results = round_results(number, root)
    benchmark = benchmark_directory(number, root)
    freeze = read(benchmark/'freeze.json')
    for name, item in freeze['files'].items():
        expected = item['sha256'] if isinstance(item, dict) else item
        check(digest(benchmark/name) == expected, 'Frozen benchmark artifact changed: '+name)
    for split, expected in [('dev', {'table': 3, 'image': 3, 'chart': 3, 'multihop': 3, 'text': 3, 'unanswerable': 3}),
                            ('test', {'table': 6, 'image': 5, 'chart': 5, 'multihop': 4, 'text': 4, 'unanswerable': 6})]:
        cases = read(benchmark/f'{split}.json')
        check(Counter(c['group'] for c in cases) == Counter(expected), 'Benchmark group counts')
        check(len({c['id'] for c in cases}) == len(cases), 'Duplicate benchmark IDs')
    selection = read(results/'selection-freeze.json')
    check(selection.get('round', 1) == number, 'Wrong selection round')
    check(selection['benchmark_freeze_sha256'] == digest(benchmark/'freeze.json'), 'Benchmark selection mismatch')
    check(selection['dev_experiment_plan_sha256'] == digest(results/'dev-experiment-plan.json'), 'Dev plan drift')
    if number == 1:
        archive = read(root/'advanced/history/round1-selected/manifest.json')
        verify_historical_hashes(archive['files'], root=root)
        verify_historical_hashes(selection['pipeline_sha256'], root=root)
        verify_historical_hashes(selection.get('evaluation_sha256', {}), root=root)
    else:
        check(selection['pipeline_sha256'] == fingerprints(), 'Selected current pipeline changed after freeze')
        for name, expected in selection.get('evaluation_sha256', {}).items():
            check(digest(root/name) == expected, 'Frozen evaluation code changed')
    current_rows = [r for r in rows if r.get('round', 1) == number]
    tests = [r for r in current_rows if r['split'] == 'test']
    check(len(tests) == 1, 'Expected exactly one Test run per published round')
    marker = read(results/'official-test.json')
    check(marker['state'] == 'completed' and marker['run_id'] == tests[0]['run_id'], 'Official Test marker/run mismatch')
    check(marker['selection_sha256'] == digest(results/'selection-freeze.json'), 'Official selection drift')
    evidence = {r['run_id']: r for r in selection['dev_evidence']}
    check(selection['chosen_dev_run'] in evidence, 'Missing selected Dev evidence')
    for row in current_rows:
        directory = root/row['path']
        config = read(directory/'config.json')
        traces = read(directory/'traces.json')
        path = case_path(config, root)
        cases = read(path)
        reviews = read(directory/'reviews-proposed.json')
        check(config['benchmark_sha256'] == digest(path), 'Run benchmark checksum')
        check({t['query_id'] for t in traces} == {c['id'] for c in cases}, 'Missing/extra trace IDs')
        check({r['query_id'] for r in reviews} == {c['id'] for c in cases}, 'Missing/extra labels')
        check(summarize(cases, traces, reviews, labels_confirmed=row['metrics']['labels_confirmed']) == row['metrics'], 'Metric drift')
        check(datetime.fromisoformat(config['started_local']) > datetime.fromisoformat(freeze['frozen_at_local']).replace(tzinfo=None), 'Benchmark not frozen before run')
        if number == 1:
            verify_historical_hashes(config['pipeline_sha256'], root=root)
        else:
            check(config['pipeline_sha256'] == selection['pipeline_sha256'], 'Current run pipeline changed')
        if row['run_id'] in evidence:
            ev = evidence[row['run_id']]
            check(digest(directory/'reviews-proposed.json') == ev['review_sha256'], 'Selected Dev review changed')
            check((ev['passed'], ev['total']) == (row['metrics']['passed'], row['metrics']['total']), 'Selected Dev score drift')
            for name, expected in ev.get('analysis_inputs_sha256', {}).items():
                check(digest(directory/name) == expected, 'Selected Dev input changed')
            for eid, expected in ev.get('analysis_api_sha256', {}).items():
                check(digest(round_results(1, root)/'api-events'/f'{eid}.json') == expected, 'Selected Dev API event changed')
        if row['split'] == 'test':
            check(config['pipeline_sha256'] == selection['pipeline_sha256'], 'Test pipeline checksum')
            check(config['config_name'] == selection['config_name'] and config['config'] == selection['config'], 'Test config mismatch')
            check(row['metrics']['total'] == 30, 'Test denominator must be all 30 published cases')
            check(datetime.fromisoformat(config['started_local']) > datetime.fromisoformat(selection['frozen_at_local']).replace(tzinfo=None), 'Selection not frozen before Test')
        for trace in traces:
            for event in trace.get('events', []):
                if event['tool'] == 'model_action':
                    allowed = {'question', 'step', 'remaining_steps', 'searches', 'calculations', 'candidate_pages', 'evidence', 'tool_errors'}
                    check(set(event['context']) <= allowed and {'question', 'evidence'} <= set(event['context']), 'Unexpected inference fields')
            for eid in trace.get('api_events', []):
                check((round_results(1, root)/'api-events'/f'{eid}.json').exists(), 'Missing response event')
    return {'round': number, 'exact_test_runs': 1, 'full_test_denominator': 30,
            'test_run_id': tests[0]['run_id'], 'test_passed': tests[0]['metrics']['passed']}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--round', type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    ledger = read(round_results(args.round)/'ledger.json')
    pages = read(DATA/'pages.json')
    chunks = read(DATA/'chunks.json')
    images = read(DATA/'render-manifest.json')
    check([p['page'] for p in pages] == list(range(1, 351)), 'Missing source pages')
    check(len(chunks) == 5493 and len({c['id'] for c in chunks}) == 5493, 'Wrong/duplicate indexed chunks')
    for page in range(1, 351):
        check(digest(DATA/'pages'/f'p{page:03}.jpg') == images['pages'][str(page)], 'Source image mismatch')
    coverage = read(DATA/'visual-coverage.json')
    check(coverage['completed_pages'] == 107 and not coverage['failures'], 'Unreported visual failures')
    rounds = [verify_round(n, ledger['runs']) for n in range(1, args.round+1)]
    shared = round_results(1)
    budget = read(shared/'budget.json')
    known = sum((Decimal(r['estimated_usd']) for r in budget['requests'] if 'estimated_usd' in r), Decimal(0))
    unknown = sum((Decimal(r['reserved_usd']) for r in budget['requests'] if 'estimated_usd' not in r), Decimal(0))
    events = [read(p) for p in (shared/'api-events').glob('*.json')]
    check(known == Decimal(usage_total(events)['estimated_usd']), 'Common ledger/event cost mismatch')
    check(known+unknown <= Decimal(budget['cap_usd']) == 5, 'Common budget exceeds cap')
    check(not any(r.get('reservation_breach') for r in budget['requests']), 'Reservation breach requires audit')
    check(len(budget['requests']) == len(events), 'Generation event/reservation count mismatch')
    if args.round == 2:
        check(known+unknown == Decimal(ledger['exposure_usd']), 'Cumulative ledger is stale')
    out = {'checks': 'passed', 'round': args.round, 'rounds': rounds,
           'benchmark_before_dev': True, 'selection_before_test': True,
           'exact_test_runs': len(rounds), 'full_test_denominator': 30, 'source_pages': 350,
           'image_hashes_checked': 350, 'indexed_chunks': 5493,
           'recorded_estimated_usd': str(known), 'unknown_reserved_usd': str(unknown),
           'semantic_review': 'Source-image labels remain separate proposals; these checks do not prove answer correctness or bonus eligibility.'}
    target = round_results(args.round)/'verification.json'
    if not (args.round == 1 and target.exists()):
        save(target, out)
    print(out)
    return out


if __name__ == '__main__':
    main()
