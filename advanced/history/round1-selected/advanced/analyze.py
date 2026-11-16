"""Rebuild strict metrics and cost tables from saved artifacts; no API calls."""
import json
import statistics
from collections import Counter
from decimal import Decimal

from scripts.summarize_results import estimate_usage, RATES
from .budget import save
from .metrics import summarize
from .source import ROOT

RESULTS=ROOT/'advanced/results'
TOKEN_FIELDS=('input_tokens','output_tokens','uncached_input_tokens','cached_input_tokens',
              'cache_write_30m_tokens','cache_write_12h_tokens')


def read(path): return json.loads(path.read_text(encoding='utf-8'))


def usage_total(events):
    amounts=[estimate_usage(e['usage']) for e in events if e.get('usage') is not None]
    return {**{k:sum(a[k] for a in amounts) for k in TOKEN_FIELDS},
            'estimated_usd':str(sum((Decimal(a['estimated_usd']) for a in amounts),Decimal(0))),
            'generation_requests':len(events),'responses_with_usage':len(amounts),
            'unknown_usage_requests':len(events)-len(amounts),
            'token_count_requests':len(events),
            'sum_api_elapsed_seconds':sum(e.get('elapsed_seconds',0) for e in events)}


def main():
    events=[read(p) for p in sorted((RESULTS/'api-events').glob('*.json'))]
    index_events=[e for e in events if e['label'].startswith('index:')]
    runs=[]
    for directory in sorted((RESULTS/'runs').iterdir()):
        if not (directory/'summary.json').exists(): continue
        config=read(directory/'config.json');traces=read(directory/'traces.json')
        cases=read(ROOT/'advanced/benchmark'/f"{config['split']}.json")
        from .source import digest
        if config['benchmark_sha256']!=digest(ROOT/'advanced/benchmark'/f"{config['split']}.json"):
            raise ValueError('Run benchmark differs from current benchmark')
        review_path=directory/'reviews-proposed.json'
        reviews=read(review_path) if review_path.exists() else []
        # Confirmation is a separate explicit artifact, never inferred from old basic labels.
        confirmation=RESULTS/'labels-confirmation.json'
        confirmed=False
        if confirmation.exists():
            from .source import digest
            obj=read(confirmation)
            confirmed=obj.get('confirmed') is True and obj.get('review_sha256',{}).get(directory.name)==digest(review_path)
        metrics=summarize(cases,traces,reviews,labels_confirmed=confirmed)
        save(directory/'metrics.json',metrics)
        requests=[e for e in events if e['label'].startswith(directory.name+':')]
        cost=usage_total(requests)
        row={'run_id':directory.name,'path':directory.relative_to(ROOT).as_posix(),
             'split':config['split'],'config_name':config['config_name'],'config':config['config'],
             'started_local':config['started_local'],'metrics':metrics,'usage_cost':cost,
             'elapsed_all_seconds':sum(t['elapsed_ms'] for t in traces)/1000,
             'median_ms':statistics.median(t['elapsed_ms'] for t in traces) if traces else None,
             'status_counts':dict(Counter(t['status'] for t in traces)),
             'tool_calls':dict(Counter(e['tool'] for t in traces for e in t.get('events',[])))}
        row['analysis_inputs_sha256']={p.name:digest(p) for p in [directory/'config.json',directory/'traces.json']+([review_path] if review_path.exists() else [])}
        row['analysis_api_sha256']={e['id']:digest(RESULTS/'api-events'/f"{e['id']}.json") for e in requests}
        runs.append(row)
    budget=read(RESULTS/'budget.json')
    known=sum((Decimal(r['estimated_usd']) for r in budget['requests'] if 'estimated_usd' in r),Decimal(0))
    unknown=sum((Decimal(r['reserved_usd']) for r in budget['requests'] if 'estimated_usd' not in r),Decimal(0))
    if known!=Decimal(usage_total(events)['estimated_usd']): raise ValueError('Ledger/event cost mismatch')
    obj={'model':'gpt-6-luna','price_date':'2026-11-16','currency':'USD',
         'rates_per_million':{k:str(v) for k,v in RATES.items()},
         'price_source':'https://developers.openai.com/api/docs/models/gpt-6-luna',
         'cost_scope':'Recorded generation response usage; estimate, not account invoice. Local compute, tax and authoring-assistant tokens are not measured. Token-count calls are logged separately, not generation usage.',
         'index':usage_total(index_events),'runs':runs,'total':usage_total(events),
         'cap_usd':budget['cap_usd'],'unknown_reserved_usd':str(unknown),
         'exposure_usd':str(known+unknown),'remaining_estimated_usd':str(Decimal(budget['cap_usd'])-known-unknown)}
    save(RESULTS/'ledger.json',obj)
    for row in runs:
        m=row['metrics'];print(row['run_id'],f"{m['passed']}/{m['total']}",row['usage_cost']['estimated_usd'],'USD')
    print('Total recorded estimate:',obj['total']['estimated_usd'],'USD; unknown reserve:',unknown)


if __name__=='__main__':main()
