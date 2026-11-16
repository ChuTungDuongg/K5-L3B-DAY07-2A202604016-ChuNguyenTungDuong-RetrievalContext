"""Evaluate the two selected agent configurations on the held-out Day 7 test."""
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
from starter.agentic import run_agent
from baseline import hit, pack_context, validate
from day6_agent import DenseRetriever, OpenAIController

CONFIGS = {'baseline': 2000, 'candidate': 4000}


def evaluate_case(case, gold, retriever, controller, *, budget, max_searches):
    """Keep gold out of both the retriever query and the agent/model input."""
    question = case['question']
    original = retriever.search(question, filters=None, top_k=3)
    original_context, original_ids = pack_context(original, budget)
    result = run_agent(question, controller, retriever, budget=budget,
                       max_searches=max_searches, top_k=3)
    searches = [e for e in result['events'] if e.get('event') == 'search']
    final_ids = set(searches[-1]['context_ids']) if searches else set()
    context_chunks = [row for event in searches for row in event['results']
                      if row['id'] in final_ids]
    original_metrics = {'hit1': None, 'hit3': None, 'context_hit': None}
    context_hit = None
    if gold is not None:
        original_metrics = {'hit1': bool(original and hit(original[0], gold)),
                            'hit3': any(hit(row, gold) for row in original[:3]),
                            'context_hit': any(row['id'] in original_ids and hit(row, gold) for row in original)}
        context_hit = any(hit(row, gold) for row in context_chunks)
    return {'query_id': case['id'], 'split': 'test', 'question': question,
            'answerable': case['answerable'], 'original_results': original,
            'original_context': original_context, 'original_context_ids': original_ids,
            'retrieval_original': original_metrics, 'agent_context_hit': context_hit,
            **result}


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description='Chạy một cấu hình agent trên toàn bộ 7 câu test')
    parser.add_argument('--config', required=True, choices=tuple(CONFIGS))
    parser.add_argument('--test-version', choices=('v1','v2'), default='v2', help='Bộ v2 là bộ test cuối cùng, v1 dùng để đối chiếu lịch sử')
    args = parser.parse_args()
    data = ROOT / 'starter' / 'data' / 'day6-A'
    question_data = ROOT / 'starter/data' / ('test-v1-archive' if args.test_version == 'v1' else 'test-v2')
    files = {'chunks.json':data/'chunks.json', 'questions-test.json':question_data/'questions-test.json',
             'agent-cases-test.json':question_data/'agent-cases-test.json'}
    chunks, questions, cases = [json.loads(files[n].read_text(encoding='utf-8')) for n in files]
    validate(chunks, questions)
    if (len(cases) != 7 or sum(c.get('answerable') is True for c in cases) != 5 or
            sum(c.get('answerable') is False for c in cases) != 2 or
            len({c['id'] for c in cases}) != len(cases)):
        raise ValueError('Tập test phải có 5 câu có đáp án và 2 câu thiếu bằng chứng, ID duy nhất')
    by_id = {q['id']: q for q in questions}
    if set(by_id) != {c['id'] for c in cases if c['answerable']}:
        raise ValueError('Câu hỏi có đáp án trong hai file không khớp')
    if any(c['split'] != 'test' or (c['answerable'] and
           (c['question'] != by_id[c['id']]['question'] or by_id[c['id']]['split'] != 'test')) for c in cases):
        raise ValueError('Tập test có split hoặc nội dung câu hỏi không khớp')
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(ROOT / '.env')
    if not os.getenv('OPENAI_API_KEY') or not os.getenv('DATABASE_URL'):
        raise SystemExit('Thiếu OPENAI_API_KEY hoặc DATABASE_URL trong .env')
    out = ROOT / 'starter' / 'results' / 'test-runs' / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + args.config + '-' + uuid4().hex[:8])
    out.mkdir(parents=True)
    cfg = {'split': 'test', 'config': args.config, 'method': 'agent-dense', 'strategy': 'A',
           'test_version': args.test_version,
           'budget_chars': CONFIGS[args.config], 'max_searches': 3, 'top_k': 3,
           'model': 'gpt-6-luna', 'max_output_tokens': 1600, 'incomplete_retry_max_output_tokens': 3200,
           'api_connection_max_retries': 2,
           'embedding_model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
           'data_sha256': {n: digest(p) for n, p in files.items()},
           'code_sha256': {n: digest(ROOT / n) for n in ('run_test.py', 'day6_agent.py', 'starter/agentic.py')},
           'note': 'Lựa chọn theo dev; test dùng để đánh giá, không dùng để chỉnh cấu hình.'}
    save(out / 'config.json', cfg)
    print('Kết quả sẽ lưu tại:', out, flush=True)
    traces = []
    try:
        from starter.day6_backend.embeddings import MyEmbedder
        from starter.day6_backend.store import PgVectorStore
        embedder = MyEmbedder(cfg['embedding_model'])
        retriever = DenseRetriever(embedder, PgVectorStore(os.environ['DATABASE_URL'], embedder.dimensions))
        client = OpenAI(timeout=60, max_retries=2)
        for n, case in enumerate(cases, 1):
            started = time.perf_counter()
            controller = OpenAIController(client, cfg['model'])
            try:
                gold = by_id[case['id']]['gold'] if case['answerable'] else None
                trace = evaluate_case(case, gold, retriever, controller, budget=cfg['budget_chars'], max_searches=3)
            except Exception as exc:
                trace = {'query_id': case['id'], 'split':'test', 'question':case['question'],
                         'answerable':case['answerable'], 'status':'error',
                         'error_type':type(exc).__name__, 'error':str(exc)}
            trace['elapsed_ms'] = round((time.perf_counter() - started) * 1000, 3)
            trace['usage'] = controller.usage
            trace['api_calls'] = controller.api_calls
            traces.append(trace)
            save(out / 'traces.json', traces)
            print(f"[{n}/{len(cases)}] {case['id']}: {trace['status']}", flush=True)
        good = [t for t in traces if t['status'] != 'error']
        answerable = [t for t in good if t['answerable']]
        summary = {'config': args.config, 'total':len(traces), 'successful':len(good), 'errors':len(traces)-len(good),
                   'retrieval_denominator':len(answerable),
                   'original_hit1':sum(t['retrieval_original']['hit1'] for t in answerable),
                   'original_hit3':sum(t['retrieval_original']['hit3'] for t in answerable),
                   'agent_context_hit':sum(t['agent_context_hit'] for t in answerable),
                   'answered':sum(t['status']=='answered' for t in good), 'abstain':sum(t['status']=='abstain' for t in good),
                   'input_tokens':sum(u['input_tokens'] for t in traces for u in t.get('usage', [])),
                   'output_tokens':sum(u['output_tokens'] for t in traces for u in t.get('usage', [])),
                   'median_ms':statistics.median(t['elapsed_ms'] for t in good) if good else None,
                   'note':'Khớp nguyên văn gold chỉ là kiểm tra sơ bộ; chấm thủ công context, citation, câu trả lời và abstention.'}
        save(out / 'summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    except Exception as exc:
        save(out / 'run-error.json', {'error_type':type(exc).__name__, 'error':str(exc), 'completed':len(traces)})
        raise


if __name__ == '__main__': main()
