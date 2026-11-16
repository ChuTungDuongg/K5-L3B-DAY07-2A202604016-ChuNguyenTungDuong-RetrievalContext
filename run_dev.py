"""Run repeatable Day 7 dev retrieval or agent experiments; never reads test."""
import argparse
import hashlib
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'starter'))
from baseline import TfidfIndex, hit, pack_context, validate
from starter.agentic import run_agent
from day6_agent import DenseRetriever, OpenAIController


def fuse(dense, lexical, top_k, rrf_k=60):
    combined = {}
    for method, rows in (('dense', dense), ('tfidf', lexical)):
        for rank, row in enumerate(rows, 1):
            item = combined.setdefault(row['id'], {**row, 'score': 0., 'ranks': {}})
            item['score'] += 1 / (rrf_k + rank)
            item['ranks'][method] = rank
    return sorted(combined.values(), key=lambda x: (-x['score'], x['id']))[:top_k]


def evaluate_result(rows, ids, gold):
    return {'hit1': bool(rows and hit(rows[0], gold)),
            'hit3': any(hit(row, gold) for row in rows[:3]),
            'context_hit': any(row['id'] in ids and hit(row, gold) for row in rows)}


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Benchmark Day 7 dev; mỗi lượt lưu thư mục riêng')
    parser.add_argument('--method', choices=['dense', 'tfidf', 'hybrid', 'agent'], required=True)
    parser.add_argument('--budget', type=int, default=2000)
    parser.add_argument('--max-searches', type=int, default=3)
    parser.add_argument('--model', default='gpt-6-luna')
    parser.add_argument('--limit', type=int, help='Chỉ chạy N câu đầu để thử; bỏ qua khi benchmark đầy đủ')
    parser.add_argument('--case-id', help='Chỉ chạy một câu dev theo ID để kiểm tra')
    args = parser.parse_args()
    if args.budget < 1 or args.max_searches < 1 or (args.limit is not None and args.limit < 1):
        parser.error('budget, max-searches và limit phải dương')
    out = ROOT / 'starter' / 'results' / 'dev-runs' / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + args.method + '-' + uuid4().hex[:8])
    out.mkdir(parents=True)
    config = {'method': args.method, 'split': 'dev', 'dataset_version': 'dev-final',
              'top_k': 3, 'budget_chars': args.budget,
              'hybrid_candidates_per_method': 10 if args.method == 'hybrid' else None,
              'max_searches': args.max_searches if args.method == 'agent' else None,
              'model': args.model if args.method == 'agent' else None,
              'embedding_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
              'stored_strategy': 'A', 'filters': 'none', 'limit': args.limit, 'case_id': args.case_id,
              'max_output_tokens': 1600 if args.method == 'agent' else None,
              'incomplete_retry_max_output_tokens': 3200 if args.method == 'agent' else None,
              'api_connection_max_retries': 0 if args.method == 'agent' else None,
              'data_sha256': {name: hashlib.sha256((ROOT / 'starter/data/day6-A' / name).read_bytes()).hexdigest()
                              for name in ('chunks.json', 'questions-dev.json', 'agent-cases-dev.json')},
              'code_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ('run_dev.py', 'starter/agentic.py', 'starter/day6_backend/embeddings.py')},
              'started_local': datetime.now().isoformat()}
    save(out / 'config.json', config)
    print('Lưu kết quả tại:', out, flush=True)
    traces = []
    try:
        root = ROOT / 'starter' / 'data' / 'day6-A'
        chunks = json.loads((root / 'chunks.json').read_text(encoding='utf-8'))
        questions = json.loads((root / 'questions-dev.json').read_text(encoding='utf-8'))
        cases = json.loads((root / 'agent-cases-dev.json').read_text(encoding='utf-8'))
        validate(chunks, questions)
        index = TfidfIndex(chunks) if args.method in ('tfidf', 'hybrid') else None
        retriever = None
        if args.method in ('dense', 'hybrid', 'agent'):
            from dotenv import load_dotenv
            load_dotenv(ROOT / '.env')
            from starter.day6_backend.embeddings import MyEmbedder
            from starter.day6_backend.store import PgVectorStore
            embedder = MyEmbedder(config['embedding_model'])
            retriever = DenseRetriever(embedder, PgVectorStore(os.getenv('DATABASE_URL'), embedder.dimensions))
        client = None
        if args.method == 'agent':
            from openai import OpenAI
            client = OpenAI(timeout=60, max_retries=0)
        inputs = cases if args.method == 'agent' else questions
        if args.case_id:
            inputs = [q for q in inputs if q['id'] == args.case_id]
            if not inputs:
                raise ValueError(f'Không có câu dev với ID {args.case_id}')
        if args.limit is not None:
            inputs = inputs[:args.limit]
        for n, q in enumerate(inputs, 1):
            started = time.perf_counter()
            trace = {'query_id': q['id'], 'split': 'dev', 'question': q['question']}
            controller = None
            try:
                if args.method == 'agent':
                    controller = OpenAIController(client, args.model)
                    result = run_agent(q['question'], controller, retriever, max_searches=args.max_searches, top_k=3, budget=args.budget)
                    trace.update(result, answerable=q['answerable'], usage=controller.usage)
                else:
                    query = q['question']
                    if args.method == 'dense': rows = retriever.search(query, filters=None, top_k=3)
                    elif args.method == 'tfidf': rows = index.search(query, top_k=3)
                    else: rows = fuse(retriever.search(query, filters=None, top_k=10), index.search(query, top_k=10), 3)
                    context, ids = pack_context(rows, args.budget)
                    trace.update(status='ok', results=rows, context=context, context_ids=ids,
                                 gold=q['gold'], **evaluate_result(rows, ids, q['gold']))
            except Exception as exc:
                trace.update(status='error', error_type=type(exc).__name__, error=str(exc),
                             usage=controller.usage if controller else [])
            trace['elapsed_ms'] = round((time.perf_counter() - started) * 1000, 3)
            if controller is not None:
                trace['api_calls'] = controller.api_calls
            traces.append(trace)
            save(out / 'traces.json', traces)
            print(f"[{n}/{len(inputs)}] {q['id']}: {trace['status']}", flush=True)
        successful = [t for t in traces if t['status'] != 'error']
        summary = {'method': args.method, 'total': len(traces), 'successful': len(successful),
                   'errors': len(traces) - len(successful),
                   'median_ms': statistics.median(t['elapsed_ms'] for t in successful) if successful else None}
        if args.method == 'agent':
            summary.update(answered=sum(t['status']=='answered' for t in successful),
                           abstain=sum(t['status']=='abstain' for t in successful),
                           input_tokens=sum(u['input_tokens'] for t in traces for u in t.get('usage', [])),
                           output_tokens=sum(u['output_tokens'] for t in traces for u in t.get('usage', [])),
                           note='Nhãn đúng/sai, citation và abstention cần chấm thủ công; lỗi được báo riêng.')
        else:
            summary.update(hit1=sum(t['hit1'] for t in successful), hit3=sum(t['hit3'] for t in successful),
                           context_hit=sum(t['context_hit'] for t in successful), metric_denominator=len(successful),
                           note='Evidence khớp nguyên văn với gold; đọc nguồn để kiểm tra evidence thay thế.')
        save(out / 'summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    except Exception as exc:
        save(out / 'run-error.json', {'error_type': type(exc).__name__, 'error': str(exc), 'completed': len(traces)})
        raise


if __name__ == '__main__':
    main()
