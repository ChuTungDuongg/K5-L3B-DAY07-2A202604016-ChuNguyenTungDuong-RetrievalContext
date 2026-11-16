"""Offline artifact checks, separate from semantic source-image review."""
from collections import Counter
from datetime import datetime
from decimal import Decimal

from .analyze import RESULTS, read
from .budget import save
from .metrics import summarize
from .run import fingerprints
from .source import DATA, ROOT, digest


def check(condition,message):
    if not condition:raise ValueError(message)


def main():
    benchmark=ROOT/'advanced/benchmark';freeze=read(benchmark/'freeze.json')
    for name,item in freeze['files'].items():check(digest(benchmark/name)==item['sha256'],'Frozen benchmark artifact changed: '+name)
    for split,expected in [('dev',{'table':3,'image':3,'chart':3,'multihop':3,'text':3,'unanswerable':3}),
                           ('test',{'table':6,'image':5,'chart':5,'multihop':4,'text':4,'unanswerable':6})]:
        cases=read(benchmark/f'{split}.json')
        check(Counter(c['group'] for c in cases)==Counter(expected),'Benchmark group counts')
        check(len({c['id'] for c in cases})==len(cases),'Duplicate benchmark IDs')
    pages=read(DATA/'pages.json');chunks=read(DATA/'chunks.json');images=read(DATA/'render-manifest.json')
    check([p['page'] for p in pages]==list(range(1,351)),'Missing source pages')
    check(len(chunks)==5493 and len({c['id'] for c in chunks})==5493,'Wrong/duplicate indexed chunks')
    for page in range(1,351):check(digest(DATA/'pages'/f'p{page:03}.jpg')==images['pages'][str(page)],'Source image mismatch')
    coverage=read(DATA/'visual-coverage.json')
    check(coverage['completed_pages']==107 and not coverage['failures'],'Unreported visual extraction failures')
    selection=read(RESULTS/'selection-freeze.json')
    check(selection['pipeline_sha256']==fingerprints(),'Selected pipeline changed after freeze')
    check(selection['benchmark_freeze_sha256']==digest(benchmark/'freeze.json'),'Benchmark selection mismatch')
    for name,expected in selection.get('evaluation_sha256',{}).items():check(digest(ROOT/name)==expected,'Frozen evaluation code changed')
    ledger=read(RESULTS/'ledger.json');tests=[r for r in ledger['runs'] if r['split']=='test']
    check(len(tests)==1,'Expected exactly one published Test run')
    for row in ledger['runs']:
        directory=ROOT/row['path'];config=read(directory/'config.json');traces=read(directory/'traces.json')
        cases=read(benchmark/f"{row['split']}.json");reviews=read(directory/'reviews-proposed.json')
        check(config['benchmark_sha256']==digest(benchmark/f"{row['split']}.json"),'Run benchmark checksum')
        current_pair=config['pipeline_sha256']==selection['pipeline_sha256']
        check({t['query_id'] for t in traces}=={c['id'] for c in cases},'Missing/extra trace IDs')
        check({r['query_id'] for r in reviews}=={c['id'] for c in cases},'Missing/extra labels')
        recomputed=summarize(cases,traces,reviews,labels_confirmed=row['metrics']['labels_confirmed'])
        check(recomputed==row['metrics'],'Metric drift')
        check(datetime.fromisoformat(config['started_local'])>datetime.fromisoformat(freeze['frozen_at_local']).replace(tzinfo=None),'Benchmark not frozen before run')
        if row['split']=='test':
            check(current_pair,'Test pipeline checksum')
            check(config['config_name']==selection['config_name'],'Test config mismatch')
            check(datetime.fromisoformat(config['started_local'])>datetime.fromisoformat(selection['frozen_at_local']).replace(tzinfo=None),'Pipeline not frozen before Test')
        for trace in traces:
            for event in trace.get('events',[]):
                if event['tool']=='model_action':
                    check(set(event['context'])=={'question','step','remaining_steps','searches','calculations','candidate_pages','evidence'},'Unexpected inference fields')
            for eid in trace.get('api_events',[]):check((RESULTS/'api-events'/f'{eid}.json').exists(),'Missing response event')
    check(Decimal(ledger['exposure_usd'])<=Decimal(ledger['cap_usd'])==5,'Budget exceeds cap')
    budget=read(RESULTS/'budget.json')
    check(not any(r.get('reservation_breach') for r in budget['requests']),'Reservation breach requires audit')
    check(len(budget['requests'])==ledger['total']['generation_requests'],'Ledger generation count mismatch')
    out={'checks':'passed','benchmark_before_dev':True,'selection_before_test':True,
         'exact_test_runs':1,'full_test_denominator':30,'source_pages':350,'image_hashes_checked':350,
         'indexed_chunks':5493,'recorded_estimated_usd':ledger['total']['estimated_usd'],
         'unknown_reserved_usd':ledger['unknown_reserved_usd'],
         'semantic_review':'Separate reviews-proposed.json; these code checks do not prove answer correctness or bonus eligibility.'}
    save(RESULTS/'verification.json',out);print(out)


if __name__=='__main__':main()
