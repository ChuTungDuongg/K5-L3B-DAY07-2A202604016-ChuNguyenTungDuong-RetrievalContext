"""Select exactly one preplanned Dev pair within a round before its Test."""
import argparse
from collections import Counter
from datetime import datetime
from decimal import Decimal

from .analyze import read, build_ledger
from .budget import save
from .run import configs_for_round, fingerprints, round_results, benchmark_directory, EVALUATION_FILES
from .source import ROOT, digest


def eligible_dev_pair(rows, number, current):
    same_round = [r for r in rows if r.get('round', 1) == number]
    if any(r['split'] == 'test' for r in same_round):
        raise ValueError('Selection must precede this round Test')
    dev = [r for r in same_round if r['split'] == 'dev' and r['pipeline_sha256'] == current]
    if Counter(r['config_name'] for r in dev) != Counter({'baseline': 1, 'candidate': 1}):
        raise ValueError('Exactly one preplanned current Dev run per config is required; no best-of repeats')
    return dev


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--round', type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    results = round_results(args.round)
    target = results/'selection-freeze.json'
    if target.exists():
        raise ValueError('Selection already frozen; do not overwrite historical selection')
    # Recompute directly from raw Dev artifacts, rather than trusting a stale ledger.
    ledger = build_ledger(args.round)
    current = fingerprints()
    dev = eligible_dev_pair(ledger['runs'], args.round, current)
    benchmark = benchmark_directory(args.round)
    plan_path = results/'dev-experiment-plan.json'
    plan = read(plan_path)
    if (plan['pipeline_sha256'] != current
            or plan['benchmark_freeze_sha256'] != digest(benchmark/'freeze.json')
            or plan.get('round', args.round) != args.round
            or plan.get('runs_planned') != {'baseline': 1, 'candidate': 1}):
        raise ValueError('Current Dev pair and benchmark were not preplanned')
    configs = configs_for_round(args.round)
    if 'configs' in plan and plan['configs'] != configs:
        raise ValueError('Plan configurations differ from runtime')
    for row in dev:
        metrics = row['metrics']
        directory = ROOT/row['path']
        cfg = read(directory/'config.json')
        if metrics['total'] != 18 or metrics['unreviewed'] or metrics['missing_results']:
            raise ValueError('Dev review incomplete')
        if cfg['config'] != configs[row['config_name']] or cfg['pipeline_sha256'] != current:
            raise ValueError('Dev pipeline/config differs from current pipeline')
        if cfg['benchmark_sha256'] != digest(benchmark/'dev.json'):
            raise ValueError('Dev benchmark changed')
        if datetime.fromisoformat(cfg['started_local']) <= datetime.fromisoformat(plan['created_local']).replace(tzinfo=None):
            raise ValueError('Dev plan must precede current Dev runs')
        required = {'config.json', 'traces.json', 'reviews-proposed.json'}
        if set(row['analysis_inputs_sha256']) != required:
            raise ValueError('Run analysis after complete grading')
        for name, expected in row['analysis_inputs_sha256'].items():
            if digest(directory/name) != expected:
                raise ValueError('Analysis input changed during selection')
        for eid, expected in row['analysis_api_sha256'].items():
            if digest(round_results(1)/'api-events'/f'{eid}.json') != expected:
                raise ValueError('API cost event changed during selection')
    selected = min(dev, key=lambda r: (-r['metrics']['passed'], r['median_ms'], Decimal(r['usage_cost']['estimated_usd'])))
    obj = {'round': args.round, 'frozen_at_local': datetime.now().astimezone().isoformat(),
           'criterion': 'Strict Dev pass count descending, then median latency ascending, then estimated cost ascending; specified before Dev.',
           'config_name': selected['config_name'], 'config': configs[selected['config_name']],
           'chosen_dev_run': selected['run_id'], 'pipeline_sha256': current,
           'benchmark_freeze_sha256': digest(benchmark/'freeze.json'),
           'dev_experiment_plan_sha256': digest(plan_path),
           'evaluation_sha256': {name: digest(ROOT/name) for name in EVALUATION_FILES},
           'dev_evidence': [{'run_id': r['run_id'], 'path': r['path'],
                             'passed': r['metrics']['passed'], 'total': r['metrics']['total'],
                             'median_ms': r['median_ms'], 'estimated_usd': r['usage_cost']['estimated_usd'],
                             'review_sha256': digest(ROOT/r['path']/'reviews-proposed.json'),
                             'analysis_inputs_sha256': r['analysis_inputs_sha256'],
                             'analysis_api_sha256': r['analysis_api_sha256']} for r in dev],
           'label_status': 'assistant_proposed_pending_learner_confirmation',
           'test_not_used_for_selection': True}
    save(results/'ledger.json', ledger)
    save(target, obj)
    print('Frozen round', args.round, ':', obj['config_name'], 'from', selected['run_id'])
    return obj


if __name__ == '__main__':
    main()
