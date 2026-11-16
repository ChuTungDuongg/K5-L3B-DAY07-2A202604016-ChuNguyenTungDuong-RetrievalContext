"""Frozen, resumable artifact-oriented advanced benchmark runner."""
import argparse
import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .agent import Agent
from .api import API
from .budget import BudgetExceeded, save
from .source import ROOT, DATA, digest

CONFIGS={'baseline':{'image_pages':3,'max_images':6,'max_steps':3},
         'candidate':{'image_pages':5,'max_images':8,'max_steps':4}}
PIPELINE_FILES=['advanced/agent.py','advanced/api.py','advanced/budget.py','advanced/retrieval.py',
                'advanced/source.py','advanced/visuals.py','advanced/run.py',
                'advanced/requirements.txt','requirements-lock.txt','starter/baseline.py',
                'starter/day6_backend/embeddings.py','starter/day6_backend/store.py',
                'starter/day6_backend/models.py','scripts/summarize_results.py']


def fingerprints():
    return {name:digest(ROOT/name) for name in PIPELINE_FILES+[
        'advanced/data/chunks.json','advanced/data/pages.json','advanced/data/regions.json',
        'advanced/data/index-manifest.json','advanced/data/index.json.gz','advanced/data/render-manifest.json']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--split',choices=['dev','test'],required=True)
    parser.add_argument('--config',choices=tuple(CONFIGS),required=True)
    args=parser.parse_args()
    benchmark=ROOT/'advanced/benchmark'
    freeze=json.loads((benchmark/'freeze.json').read_text(encoding='utf-8'))
    # Freeze format is documented by the source-checking benchmark author.
    path=benchmark/f'{args.split}.json'
    expected=freeze.get('files',{}).get(path.name)
    if isinstance(expected,dict):expected=expected.get('sha256')
    if expected is None:expected=freeze.get(f'{args.split}_sha256')
    if not expected or digest(path)!=expected:raise ValueError('Benchmark freeze hash mismatch')
    config=CONFIGS[args.config]
    hashes=fingerprints()
    if args.split=='test':
        selection=json.loads((ROOT/'advanced/results/selection-freeze.json').read_text(encoding='utf-8'))
        if selection['config_name']!=args.config or selection['pipeline_sha256']!=hashes or selection['config']!=config:
            raise ValueError('Test requires the exact pipeline/config frozen after dev')
    cases=json.loads(path.read_text(encoding='utf-8'))
    timestamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    run_id=f'{timestamp}-{args.split}-{args.config}-{uuid4().hex[:8]}'
    directory=ROOT/'advanced/results/runs'/run_id
    directory.mkdir(parents=True)
    cfg={'run_id':run_id,'split':args.split,'config_name':args.config,'config':config,'model':'gpt-6-luna',
         'benchmark_sha256':digest(path),'pipeline_sha256':hashes,'started_local':datetime.now().isoformat(),
         'grading':'strict pass/fail; all published cases, including errors, remain in denominator'}
    save(directory/'config.json',cfg)
    from .retrieval import Retriever
    retriever=Retriever();api=API();traces=[]
    print('Run:',directory,flush=True)
    for n,case in enumerate(cases,1):
        started=time.perf_counter();agent=Agent(retriever,api,config)
        trace={'query_id':case['id'],'question':case['question'],'split':args.split,'group':case['group']}
        try:trace.update(agent.run(case['question'],run_id+':'+case['id']))
        except Exception as exc:
            trace.update(getattr(agent,'partial',{}),status='error',error_type=type(exc).__name__,error=str(exc))
        trace['elapsed_ms']=round((time.perf_counter()-started)*1000,3)
        traces.append(trace);save(directory/'traces.json',traces)
        print(f"[{n}/{len(cases)}] {case['id']}: {trace['status']}",flush=True)
        if trace.get('error_type')=='BudgetExceeded':
            # Remaining cases have no result and are failures in strict aggregation.
            break
    save(directory/'summary.json',{'total_published':len(cases),'completed':len(traces),
                                  'errors':sum(t['status']=='error' for t in traces),
                                  'elapsed_all_seconds':sum(t['elapsed_ms'] for t in traces)/1000,
                                  'median_ms':statistics.median(t['elapsed_ms'] for t in traces) if traces else None,
                                  'budget_snapshot':api.budget.snapshot(),
                                  'labels_status':'not graded; no quality metric inferred from citation IDs'})


if __name__=='__main__':main()
