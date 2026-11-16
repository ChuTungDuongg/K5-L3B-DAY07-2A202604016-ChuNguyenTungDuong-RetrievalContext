"""Round-aware, frozen artifact-oriented advanced benchmark runner."""
import argparse
import copy
import json
import statistics
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .agent import Agent
from .api import API
from .budget import save
from .source import ROOT, digest, verify_images

CONFIGS = {'baseline': {'image_pages': 3, 'max_images': 6, 'max_steps': 3},
           'candidate': {'image_pages': 5, 'max_images': 8, 'max_steps': 4}}
PIPELINE_FILES = ['advanced/agent.py', 'advanced/api.py', 'advanced/budget.py',
                  'advanced/citations.py', 'advanced/retrieval.py', 'advanced/source.py',
                  'advanced/visuals.py', 'advanced/run.py', 'advanced/requirements.txt',
                  'requirements-lock.txt', 'starter/baseline.py',
                  'starter/day6_backend/embeddings.py', 'starter/day6_backend/store.py',
                  'starter/day6_backend/models.py', 'scripts/summarize_results.py']
DATA_FILES = ['advanced/data/chunks.json', 'advanced/data/pages.json',
              'advanced/data/regions.json', 'advanced/data/index-manifest.json',
              'advanced/data/index.json.gz', 'advanced/data/render-manifest.json']
EVALUATION_FILES = ['advanced/metrics.py', 'advanced/analyze.py', 'advanced/select.py',
                    'advanced/official_test.py', 'advanced/verify.py']


def round_results(number=1, root=None):
    if type(number) is not int or number not in (1, 2):
        raise ValueError('Supported experiment rounds are 1 and 2')
    base = Path(ROOT if root is None else root)/'advanced/results'
    return base if number == 1 else base/f'round{number}'


def benchmark_directory(number=1, root=None):
    round_results(number, root)
    base = Path(ROOT if root is None else root)/'advanced/benchmark'
    return base if number == 1 else base/f'round{number}'


def configs_for_round(number=1):
    round_results(number)
    configs = copy.deepcopy(CONFIGS)
    if number == 2:
        for config in configs.values():
            config.update(review_before_answer=True, citation_policy='full_page_specific_locator')
    return configs


def case_path(config, root=None):
    root = Path(ROOT if root is None else root)
    if config['split'] not in ('dev', 'test'):
        raise ValueError('Invalid benchmark split')
    expected = benchmark_directory(config.get('round', 1), root)/f"{config['split']}.json"
    path = root/config.get('benchmark_path', expected.relative_to(root).as_posix())
    if path.resolve() != expected.resolve():
        raise ValueError('Run benchmark path does not belong to its recorded round/split')
    return path


def run_directories(number=1, root=None):
    """Return historical run paths without loading benchmark questions."""
    paths = []
    for current in range(1, number+1):
        directory = round_results(current, root)/'runs'
        if directory.exists():
            paths.extend(p for p in sorted(directory.iterdir()) if p.is_dir() and (p/'config.json').exists())
    return paths


def fingerprints():
    return {name: digest(ROOT/name) for name in PIPELINE_FILES+DATA_FILES}


def verify_selection(selection, name, config, hashes, benchmark_freeze_hash, *, number=None):
    if (selection['config_name'] != name or selection['pipeline_sha256'] != hashes
            or selection['config'] != config
            or selection['benchmark_freeze_sha256'] != benchmark_freeze_hash
            or (number is not None and selection.get('round', 1) != number)):
        raise ValueError('Test requires the exact round/benchmark/pipeline/config frozen after dev')
    for path, expected in selection.get('evaluation_sha256', {}).items():
        if digest(ROOT/path) != expected:
            raise ValueError('Evaluation code differs from selection freeze')


def verify_benchmark(path, freeze):
    expected = freeze.get('files', {}).get(path.name)
    if isinstance(expected, dict):
        expected = expected.get('sha256')
    if expected is None:
        expected = freeze.get(path.stem+'_sha256')
    if not expected or digest(path) != expected:
        raise ValueError('Benchmark freeze hash mismatch')


def main(argv=None, *, official=False):
    parser = argparse.ArgumentParser()
    parser.add_argument('--round', type=int, choices=(1, 2), default=1)
    parser.add_argument('--split', choices=('dev', 'test'), required=True)
    parser.add_argument('--config', choices=tuple(CONFIGS), required=True)
    args = parser.parse_args(argv)
    benchmark = benchmark_directory(args.round)
    freeze = json.loads((benchmark/'freeze.json').read_text(encoding='utf-8'))
    path = benchmark/f'{args.split}.json'
    verify_benchmark(path, freeze)
    config = configs_for_round(args.round)[args.config]
    hashes = fingerprints()
    results = round_results(args.round)
    if args.split == 'test':
        selection = json.loads((results/'selection-freeze.json').read_text(encoding='utf-8'))
        verify_selection(selection, args.config, config, hashes, digest(benchmark/'freeze.json'), number=args.round)
        if official:
            marker = json.loads((results/'official-test.json').read_text(encoding='utf-8'))
            if marker['state'] != 'claimed' or marker['selection_sha256'] != digest(results/'selection-freeze.json'):
                raise ValueError('Official Test requires an active matching claim')
    elif args.round == 2:
        plan = json.loads((results/'dev-experiment-plan.json').read_text(encoding='utf-8'))
        if plan['pipeline_sha256'] != hashes or plan['benchmark_freeze_sha256'] != digest(benchmark/'freeze.json'):
            raise ValueError('Dev requires the current predeclared pipeline and benchmark')
        if plan.get('round', 2) != 2 or plan.get('runs_planned') != {'baseline': 1, 'candidate': 1}:
            raise ValueError('Dev plan must declare one attempt per round/config')
        if 'configs' in plan and plan['configs'] != configs_for_round(2):
            raise ValueError('Dev configs differ from the predeclared plan')
        for directory in run_directories(2):
            prior = json.loads((directory/'config.json').read_text(encoding='utf-8'))
            if prior.get('round', 1) == 2 and (prior['split'] == 'test' or
                    (prior['config_name'] == args.config and prior['pipeline_sha256'] == hashes)):
                raise ValueError('No repeated planned Dev attempts or Dev after Test')
    verify_images()
    cases = json.loads(path.read_text(encoding='utf-8'))
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    round_tag = '' if args.round == 1 else f'-r{args.round}'
    run_id = f'{timestamp}{round_tag}-{args.split}-{args.config}-{uuid4().hex[:8]}'
    directory = results/'runs'/run_id
    directory.mkdir(parents=True)
    cfg = {'run_id': run_id, 'round': args.round, 'split': args.split, 'config_name': args.config,
           'config': config, 'model': 'gpt-6-luna', 'benchmark_path': path.relative_to(ROOT).as_posix(),
           'benchmark_sha256': digest(path), 'pipeline_sha256': hashes,
           'benchmark_freeze_sha256': digest(benchmark/'freeze.json'),
           'started_local': datetime.now().isoformat(),
           'execution_role': 'official' if official else ('dev' if args.split == 'dev' else 'diagnostic'),
           'grading': 'strict pass/fail; all published cases, including errors, remain in denominator'}
    save(directory/'config.json', cfg)
    from .retrieval import Retriever
    retriever = Retriever()
    api = API()
    traces = []
    print('Run:', directory, flush=True)
    for n, case in enumerate(cases, 1):
        started = time.perf_counter()
        agent = Agent(retriever, api, config)
        trace = {'query_id': case['id'], 'question': case['question'], 'split': args.split, 'group': case['group']}
        try:
            trace.update(agent.run(case['question'], run_id+':'+case['id']))
        except Exception as exc:
            trace.update(getattr(agent, 'partial', {}), status='error', error_type=type(exc).__name__, error=str(exc))
        trace['elapsed_ms'] = round((time.perf_counter()-started)*1000, 3)
        traces.append(trace)
        save(directory/'traces.json', traces)
        print(f"[{n}/{len(cases)}] {case['id']}: {trace['status']}", flush=True)
        if trace.get('error_type') == 'BudgetExceeded':
            break
    save(directory/'summary.json', {'total_published': len(cases), 'completed': len(traces),
                                  'errors': sum(t['status'] == 'error' for t in traces),
                                  'elapsed_all_seconds': sum(t['elapsed_ms'] for t in traces)/1000,
                                  'median_ms': statistics.median(t['elapsed_ms'] for t in traces) if traces else None,
                                  'budget_snapshot': api.budget.snapshot(),
                                  'labels_status': 'not graded; no quality metric inferred from citation IDs'})
    return run_id


if __name__ == '__main__':
    main()
