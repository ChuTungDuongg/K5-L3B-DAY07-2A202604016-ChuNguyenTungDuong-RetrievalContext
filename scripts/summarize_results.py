"""Create an auditable ledger from stored trace usage, not from guessed invoices."""
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATES = {'input':Decimal('0.10'), 'cached':Decimal('0.01'), 'write30':Decimal('0.125'),
         'write12':Decimal('0.25'), 'output':Decimal('0.50')}


def dataset_version(split, config, traces):
    """Identify the input dataset, including runs restricted to one shared case."""
    if config.get('dataset_version'):
        return config['dataset_version']
    if split == 'test':
        return 'test-v2' if traces and traces[0]['query_id'].startswith('v2-') else 'test-v1'
    recorded = config.get('data_sha256', {})
    for version, folder in (('dev-final', 'day6-A'), ('dev-original', 'dev-original-archive')):
        for name in ('questions-dev.json', 'agent-cases-dev.json'):
            path = ROOT / 'starter/data' / folder / name
            if recorded.get(name) and recorded[name] == hashlib.sha256(path.read_bytes()).hexdigest():
                return version
    ids = {t['query_id'] for t in traces}
    if 'dev-extra-compliance' in ids:
        return 'dev-final'
    if 'dev-auto-373' in ids:
        return 'dev-original'
    return 'dev-unversioned'


def estimate_usage(usage):
    details = usage.get('input_tokens_details') or {}
    cached = details.get('cached_tokens',0) or 0
    writes = details.get('cache_write_tokens',0) or 0
    breakdown = details.get('cache_write_tokens_details') or {}
    write12 = breakdown.get('ttl_12h_tokens',0) or 0
    write30 = writes - write12
    uncached = usage.get('input_tokens',0) - cached - writes
    if min(uncached, cached, write12, write30) < 0:
        raise ValueError('Invalid usage breakdown')
    output = usage.get('output_tokens',0)
    cost = (uncached*RATES['input'] + cached*RATES['cached'] + write30*RATES['write30'] +
            write12*RATES['write12'] + output*RATES['output']) / 1_000_000
    return {'uncached_input_tokens':uncached, 'cached_input_tokens':cached,
            'cache_write_30m_tokens':write30, 'cache_write_12h_tokens':write12,
            'input_tokens':usage.get('input_tokens',0), 'output_tokens':output,
            'estimated_usd':format(cost.quantize(Decimal('0.0000000001')), 'f')}


def main():
    rows = []
    for folder in ('dev-runs', 'test-runs'):
        for directory in sorted((ROOT / 'starter/results' / folder).iterdir()):
            if not directory.is_dir() or not (directory/'traces.json').exists():
                continue
            traces = json.loads((directory/'traces.json').read_text(encoding='utf-8'))
            config = json.loads((directory/'config.json').read_text(encoding='utf-8'))
            summary = json.loads((directory/'summary.json').read_text(encoding='utf-8')) if (directory/'summary.json').exists() else {}
            metrics_path = directory/'agent-metrics.json'
            if not metrics_path.exists(): metrics_path = directory/'agent-metrics-proposed.json'
            metrics = json.loads(metrics_path.read_text(encoding='utf-8')) if metrics_path.exists() else None
            amounts = [estimate_usage(u) for t in traces for u in t.get('usage',[])]
            amount = {key:sum(row[key] for row in amounts) for key in ('input_tokens','output_tokens','uncached_input_tokens','cached_input_tokens','cache_write_30m_tokens','cache_write_12h_tokens')}
            amount['estimated_usd'] = format(sum((Decimal(a['estimated_usd']) for a in amounts),Decimal(0)).quantize(Decimal('0.0000000001')),'f')
            successful = [t for t in traces if t.get('status') != 'error']
            row = {'run_id':directory.name,'path':directory.relative_to(ROOT).as_posix(),
                   'split':'dev' if folder=='dev-runs' else 'test', 'config':config,
                   'dataset_version':dataset_version('dev' if folder=='dev-runs' else 'test', config, traces),
                   'total':len(traces),'successful':len(successful),'errors':len(traces)-len(successful),
                   'elapsed_all_seconds':sum(t.get('elapsed_ms',0) for t in traces)/1000,
                   'median_ms':summary.get('median_ms'),
                   'recorded_usage_responses':len(amounts), 'usage_cost':amount,
                   'search_distribution':dict(Counter(sum(e.get('event')=='search' for e in t.get('events',[])) for t in successful)),
                   'metrics':metrics,'summary':summary,
                   'error_counts':dict(Counter(t.get('error_type','unknown') for t in traces if t.get('status')=='error'))}
            rows.append(row)
    total_cost = sum((Decimal(row['usage_cost']['estimated_usd']) for row in rows),Decimal(0))
    obj = {'price_date':'2026-11-16','model':'gpt-6-luna','currency':'USD',
           'source':'https://developers.openai.com/api/docs/models/gpt-6-luna',
           'rates_per_million':{key:str(val) for key,val in RATES.items()},
           'assumptions':'Standard short-context public prices; no regional/tier premium or tax. Recorded response usage only. Missing usage, API sanity calls, question generation, unrecorded debug requests and local compute are excluded. This is not an account invoice.',
           'total_recorded_input_tokens':sum(r['usage_cost']['input_tokens'] for r in rows),
           'total_recorded_output_tokens':sum(r['usage_cost']['output_tokens'] for r in rows),
           'total_estimated_usd':format(total_cost.quantize(Decimal('0.0000000001')),'f'), 'runs':rows}
    output = ROOT/'results'
    output.mkdir(exist_ok=True)
    (output/'run_ledger.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"Ledger: {len(rows)} runs, recorded cost estimate USD {obj['total_estimated_usd']}")


if __name__ == '__main__': main()
