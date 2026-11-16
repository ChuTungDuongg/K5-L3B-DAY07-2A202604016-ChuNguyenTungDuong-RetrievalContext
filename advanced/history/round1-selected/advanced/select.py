"""Choose once using fully reviewed Dev only, before running any Test."""
from datetime import datetime
from decimal import Decimal
from collections import Counter

from .analyze import RESULTS, read
from .budget import save
from .run import CONFIGS, fingerprints
from .source import ROOT, digest


def main():
    target=RESULTS/'selection-freeze.json'
    if target.exists():raise ValueError('Selection already frozen; do not overwrite historical selection')
    ledger=read(RESULTS/'ledger.json')
    if any(r['split']=='test' for r in ledger['runs']):raise ValueError('Selection must precede Test')
    current=fingerprints()
    dev=[r for r in ledger['runs'] if r['split']=='dev' and read(ROOT/r['path']/'config.json')['pipeline_sha256']==current]
    if Counter(r['config_name'] for r in dev)!=Counter({'baseline':1,'candidate':1}):
        raise ValueError('Exactly one preplanned current Dev run per config is required; no best-of repeats')
    plan=read(RESULTS/'dev-experiment-plan.json')
    if plan['pipeline_sha256']!=current:raise ValueError('Current Dev pair was not preplanned')
    for row in dev:
        m=row['metrics'];directory=ROOT/row['path'];cfg=read(directory/'config.json')
        if m['total']!=18 or m['unreviewed'] or m['missing_results']:raise ValueError('Dev review incomplete')
        if cfg['pipeline_sha256']!=current:raise ValueError('Dev pipeline differs from current pipeline')
        if cfg['benchmark_sha256']!=digest(ROOT/'advanced/benchmark/dev.json'):raise ValueError('Dev benchmark changed')
        if datetime.fromisoformat(cfg['started_local'])<=datetime.fromisoformat(plan['created_local']).replace(tzinfo=None):
            raise ValueError('Dev plan must precede current Dev runs')
        for name,expected in row['analysis_inputs_sha256'].items():
            if digest(directory/name)!=expected:raise ValueError('Recompute analysis after input changes')
        if 'reviews-proposed.json' not in row['analysis_inputs_sha256']:raise ValueError('Run analysis after grading')
        for eid,expected in row['analysis_api_sha256'].items():
            if digest(RESULTS/'api-events'/f'{eid}.json')!=expected:raise ValueError('API cost event changed since analysis')
    selected=min(dev,key=lambda r:(-r['metrics']['passed'],r['median_ms'],Decimal(r['usage_cost']['estimated_usd'])))
    obj={'frozen_at_local':datetime.now().astimezone().isoformat(),
         'criterion':'Strict Dev pass count descending, then median latency ascending, then estimated cost ascending; specified before Dev in design document.',
         'config_name':selected['config_name'],'config':CONFIGS[selected['config_name']],
         'chosen_dev_run':selected['run_id'],'pipeline_sha256':current,
         'benchmark_freeze_sha256':digest(ROOT/'advanced/benchmark/freeze.json'),
         'dev_experiment_plan_sha256':digest(RESULTS/'dev-experiment-plan.json'),
         'evaluation_sha256':{name:digest(ROOT/name) for name in ['advanced/metrics.py','advanced/analyze.py','advanced/select.py','advanced/official_test.py']},
         'dev_evidence':[{'run_id':r['run_id'],'passed':r['metrics']['passed'],'total':r['metrics']['total'],
                          'median_ms':r['median_ms'],'estimated_usd':r['usage_cost']['estimated_usd'],
                          'review_sha256':digest(ROOT/r['path']/'reviews-proposed.json')} for r in dev],
         'label_status':'assistant_proposed_pending_learner_confirmation',
         'test_not_used_for_selection':True}
    save(target,obj);print('Frozen:',obj['config_name'],'from',selected['run_id'])


if __name__=='__main__':main()
