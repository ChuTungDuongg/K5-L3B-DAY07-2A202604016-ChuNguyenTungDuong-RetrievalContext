"""Offline artifact consistency checks. Does not judge semantic label correctness."""
import argparse
import ast
import gzip
import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.summarize_results import dataset_version, estimate_usage
from starter.agent_metrics import aggregate
from starter.baseline import hit, validate
from starter.restore_day6 import validate_snapshot


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_dataset(folder, split, n, chunks):
    questions = read(folder / f'questions-{split}.json')
    cases = read(folder / f'agent-cases-{split}.json')
    validate(chunks, questions)
    require(len(questions) == n, f'{folder}: answerable count')
    require(len(cases) == n + 2 and sum(c['answerable'] is True for c in cases) == n,
            f'{folder}: case counts')
    require(len({c['id'] for c in cases}) == len(cases), f'{folder}: duplicate IDs')
    require(all(c['split'] == split for c in cases), f'{folder}: split mismatch')
    by_id = {q['id']: q for q in questions}
    require(set(by_id) == {c['id'] for c in cases if c['answerable']}, f'{folder}: IDs mismatch')
    require(all(c['question'] == by_id[c['id']]['question'] for c in cases if c['answerable']),
            f'{folder}: question mismatch')
    require(all(c.get('absence_reason') for c in cases if not c['answerable']),
            f'{folder}: missing absence rationale')
    return questions, cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Also inspect actual Git index bytes for secrets')
    args = parser.parse_args()
    snapshot_path = ROOT / 'data/day6_index_A.json.gz'
    expected = (ROOT / 'data/day6_index_A.sha256').read_text().split()[0]
    require(hashlib.sha256(snapshot_path.read_bytes()).hexdigest() == expected, 'Snapshot checksum')
    snapshot = json.loads(gzip.decompress(snapshot_path.read_bytes()))
    validate_snapshot(snapshot)
    chunks = read(ROOT / 'starter/data/day6-A/chunks.json')
    require(len(chunks) == 273 and snapshot['dimensions'] == 384, 'Snapshot size/dimensions')
    plain = [{k: v for k, v in c.items() if k != 'embedding'} for c in snapshot['chunks']]
    require({c['id']: c for c in plain} == {c['id']: c for c in chunks}, 'Snapshot vs chunks JSON')
    dev, dev_cases = check_dataset(ROOT / 'starter/data/day6-A', 'dev', 15, chunks)
    test, test_cases = check_dataset(ROOT / 'starter/data/test-v2', 'test', 5, chunks)
    normalized = lambda text: ' '.join(text.casefold().split())
    require(len({normalized(c['question']) for c in dev_cases}) == 17, 'Dev has repeated questions')
    require(len({normalized(c['question']) for c in test_cases}) == 7, 'Test has repeated questions')
    require(not ({normalized(c['question']) for c in dev_cases} &
                 {normalized(c['question']) for c in test_cases}), 'Questions shared across dev/test')
    corpus = '\n'.join(c['text'] for c in chunks).casefold()
    for name in ('Velmora Labs', 'Ardenwick Systems', 'Norvale Prism', 'Calderwick Grove'):
        require(name.casefold() not in corpus, f'Fictional entity appeared: {name}')
    print('OK: snapshot, 273 chunks, 15+2 dev and 5+2 test, evidence and split consistency')

    ledger = read(ROOT / 'results/run_ledger.json')
    input_tokens = output_tokens = 0
    cost = Decimal(0)
    reviewed = 0
    for row in ledger['runs']:
        directory = ROOT / row['path']
        traces, config = read(directory / 'traces.json'), read(directory / 'config.json')
        require(row['dataset_version'] == dataset_version(row['split'], config, traces), 'Dataset version')
        successful = [t for t in traces if t.get('status') != 'error']
        require((row['total'], row['successful'], row['errors']) ==
                (len(traces), len(successful), len(traces) - len(successful)), f'{directory}: status counts')
        usage = [estimate_usage(u) for t in traces for u in t.get('usage', [])]
        for key in ('input_tokens', 'output_tokens', 'uncached_input_tokens', 'cached_input_tokens',
                    'cache_write_30m_tokens', 'cache_write_12h_tokens'):
            require(row['usage_cost'][key] == sum(u[key] for u in usage), f'{directory}: usage {key}')
        run_cost = sum((Decimal(u['estimated_usd']) for u in usage), Decimal(0))
        require(run_cost == Decimal(row['usage_cost']['estimated_usd']), f'{directory}: cost')
        input_tokens += row['usage_cost']['input_tokens']
        output_tokens += row['usage_cost']['output_tokens']
        cost += run_cost
        if not (directory / 'reviews.json').exists():
            continue
        version = row['dataset_version']
        data_folder = {'dev-final': 'day6-A', 'dev-original': 'dev-original-archive',
                       'test-v1': 'test-v1-archive', 'test-v2': 'test-v2'}.get(version)
        require(data_folder is not None, f'{directory}: cannot select versioned labels')
        folder = ROOT / 'starter/data' / data_folder
        cases = read(folder / f"agent-cases-{row['split']}.json")
        reviews = read(directory / 'reviews.json')
        actual = {'split': row['split'], **aggregate(cases, traces, reviews)}
        stored = read(directory / 'agent-metrics.json')
        require(all(stored[k] == v for k, v in actual.items()), f'{directory}: label metric mismatch')
        questions = {q['id']: q for q in read(folder / f"questions-{row['split']}.json")}
        if 'context_exact' in stored:
            n = N = 0
            for t in successful:
                if t['query_id'] not in questions:
                    continue
                N += 1
                events = [e for e in t.get('events', []) if e.get('event') == 'search']
                ids = set(events[-1]['context_ids']) if events else set()
                n += any(hit(c, questions[t['query_id']]['gold']) for e in events
                         for c in e['results'] if c['id'] in ids)
            require(stored['context_exact'] == {'n': n, 'N': N}, f'{directory}: context metric')
        require(row['metrics'] == stored, f'{directory}: ledger metrics stale')
        reviewed += 1
    require((input_tokens, output_tokens, cost) ==
            (ledger['total_recorded_input_tokens'], ledger['total_recorded_output_tokens'],
             Decimal(ledger['total_estimated_usd'])), 'Ledger total mismatch')
    print(f'OK: {len(ledger["runs"])} runs, {reviewed} reviewed metrics, tokens and estimated costs')

    template = (ROOT / 'report/individual/MSSV_HoTen.md').read_text(encoding='utf-8')
    report_path = ROOT / 'report/individual/2A202604016_ChuNguyenTungDuong.md'
    report = report_path.read_text(encoding='utf-8')
    headings = lambda text: [line for line in text.splitlines() if line.startswith('## ')]
    require(headings(report) == headings(template), 'Teacher report sections changed')
    for line in template.splitlines():
        if line.startswith('| ') and ('Cấu hình |' in line or 'Cấu hình / split' in line or
                                       'Query ID' in line or 'Nhóm test' in line):
            require(line in report, f'Teacher table columns changed: {line}')
    require('Chu Nguyễn Tùng Dương' in report and '2A202604016' in report, 'Student identity')
    require('@@' not in report, 'Unfilled generated field')
    for label, link in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', report):
        if '://' not in link and not link.startswith('#'):
            require((report_path.parent / link.split('#')[0]).exists(), f'Broken report link: {label}')
    tree = ast.parse((ROOT / 'starter/agentic.py').read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        require(not isinstance(node, ast.Pass) and not (isinstance(node, ast.Constant) and node.value is Ellipsis),
                'Unimplemented starter body')
    print('OK: teacher report sections/columns, local links, identity and concrete starter bodies')

    if args.staged:
        paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
        secret = re.compile(rb'(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|ghp_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
        for path in filter(None, paths):
            require(Path(path).name != '.env' and not Path(path).name.startswith('.env.local'),
                    f'Environment file in Git: {path}')
            data = subprocess.check_output(['git', 'show', ':' + path], cwd=ROOT)
            require(not secret.search(data), f'Possible secret in Git index: {path}')
        print('OK: Git index excludes .env and recognizable API/private-key values')
    print('No API calls. Semantic grounding and source permissions still require human review.')


if __name__ == '__main__':
    main()
