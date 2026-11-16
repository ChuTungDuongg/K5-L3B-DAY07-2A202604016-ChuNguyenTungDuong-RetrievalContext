"""Rebuild round-aware metrics and a common-budget cost ledger without API calls."""
import argparse
import json
import statistics
from collections import Counter
from decimal import Decimal

from scripts.summarize_results import estimate_usage, RATES
from .budget import save
from .metrics import summarize
from .run import case_path, round_results, run_directories
from .source import ROOT, digest

RESULTS = ROOT/'advanced/results'
TOKEN_FIELDS = ('input_tokens', 'output_tokens', 'uncached_input_tokens', 'cached_input_tokens',
                'cache_write_30m_tokens', 'cache_write_12h_tokens')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def usage_total(events):
    amounts = [estimate_usage(e['usage']) for e in events if e.get('usage') is not None]
    return {**{k: sum(a[k] for a in amounts) for k in TOKEN_FIELDS},
            'estimated_usd': str(sum((Decimal(a['estimated_usd']) for a in amounts), Decimal(0))),
            'generation_requests': len(events), 'responses_with_usage': len(amounts),
            'unknown_usage_requests': len(events)-len(amounts), 'token_count_requests': len(events),
            'sum_api_elapsed_seconds': sum(e.get('elapsed_seconds', 0) for e in events)}


def build_ledger(number=1, *, root=None):
    root = ROOT if root is None else root
    shared = round_results(1, root)
    events = [read(p) for p in sorted((shared/'api-events').glob('*.json'))]
    runs = []
    for directory in run_directories(number, root):
        if not (directory/'summary.json').exists():
            continue
        config = read(directory/'config.json')
        current_round = config.get('round', 1)
        path = case_path(config, root)
        if config['benchmark_sha256'] != digest(path):
            raise ValueError('Run benchmark differs from its recorded benchmark')
        cases = read(path)
        traces = read(directory/'traces.json')
        review_path = directory/'reviews-proposed.json'
        reviews = read(review_path) if review_path.exists() else []
        confirmation = round_results(current_round, root)/'labels-confirmation.json'
        confirmed = False
        if confirmation.exists() and review_path.exists():
            obj = read(confirmation)
            confirmed = obj.get('confirmed') is True and obj.get('review_sha256', {}).get(directory.name) == digest(review_path)
        metrics = summarize(cases, traces, reviews, labels_confirmed=confirmed)
        # Earlier rounds are historical evidence and are never rewritten.
        if current_round == number and not (number == 1 and (root/'advanced/history/round1-selected/manifest.json').exists()):
            save(directory/'metrics.json', metrics)
        requests = [e for e in events if e['label'].startswith(directory.name+':')]
        cost = usage_total(requests)
        row = {'run_id': directory.name, 'path': directory.relative_to(root).as_posix(),
               'round': current_round, 'split': config['split'], 'config_name': config['config_name'],
               'config': config['config'], 'pipeline_sha256': config.get('pipeline_sha256', {}),
               'benchmark_path': path.relative_to(root).as_posix(),
               'started_local': config['started_local'], 'metrics': metrics, 'usage_cost': cost,
               'elapsed_all_seconds': sum(t['elapsed_ms'] for t in traces)/1000,
               'median_ms': statistics.median(t['elapsed_ms'] for t in traces) if traces else None,
               'status_counts': dict(Counter(t['status'] for t in traces)),
               'tool_calls': dict(Counter(e['tool'] for t in traces for e in t.get('events', [])))}
        inputs = [directory/'config.json', directory/'traces.json']+([review_path] if review_path.exists() else [])
        row['analysis_inputs_sha256'] = {p.name: digest(p) for p in inputs}
        row['analysis_api_sha256'] = {e['id']: digest(shared/'api-events'/f"{e['id']}.json") for e in requests}
        runs.append(row)
    budget = read(shared/'budget.json')
    known = sum((Decimal(r['estimated_usd']) for r in budget['requests'] if 'estimated_usd' in r), Decimal(0))
    unknown = sum((Decimal(r['reserved_usd']) for r in budget['requests'] if 'estimated_usd' not in r), Decimal(0))
    if known != Decimal(usage_total(events)['estimated_usd']):
        raise ValueError('Ledger/event cost mismatch')
    return {'round': number, 'model': 'gpt-6-luna', 'price_date': '2026-11-16', 'currency': 'USD',
            'rates_per_million': {k: str(v) for k, v in RATES.items()},
            'price_source': 'https://developers.openai.com/api/docs/models/gpt-6-luna',
            'cost_scope': 'All advanced rounds share one budget. Recorded generation usage is an estimate, not an invoice. Local compute, tax and authoring-assistant tokens are not measured.',
            'index': usage_total([e for e in events if e['label'].startswith('index:')]),
            'runs': runs, 'total': usage_total(events), 'cap_usd': budget['cap_usd'],
            'unknown_reserved_usd': str(unknown), 'exposure_usd': str(known+unknown),
            'remaining_estimated_usd': str(Decimal(budget['cap_usd'])-known-unknown)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--round', type=int, choices=(1, 2), default=1)
    args = parser.parse_args(argv)
    target = round_results(args.round)/'ledger.json'
    if args.round == 1 and target.exists() and (ROOT/'advanced/history/round1-selected/manifest.json').exists():
        obj = read(target)
        print('Historical Round 1 ledger preserved; use --round 2 for the cumulative ledger.')
    else:
        obj = build_ledger(args.round)
        save(target, obj)
    for row in obj['runs']:
        metrics = row['metrics']
        print(row['run_id'], f"{metrics['passed']}/{metrics['total']}", row['usage_cost']['estimated_usd'], 'USD')
    print('Total recorded estimate:', obj['total']['estimated_usd'], 'USD; unknown reserve:', obj['unknown_reserved_usd'])
    return obj


if __name__ == '__main__':
    main()
