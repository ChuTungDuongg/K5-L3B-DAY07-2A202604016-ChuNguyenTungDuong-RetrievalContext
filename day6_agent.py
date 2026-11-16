"""Agent Day 7: OpenAI controller and dense retrieval over the Day 6 store."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DAY6_STARTER = ROOT.parent / 'K5-L3B-DAY06-ChuNguyenTungDuong-2A202604016-DataIngestion' / 'starter'


from starter.agentic import Controller as OpenAIController, Retriever as DenseRetriever


def main():
    parser = argparse.ArgumentParser(description='Search Day 6 vectors and answer with OpenAI')
    parser.add_argument('--question', help='Question to ask; prompts if omitted')
    parser.add_argument('--model', default='gpt-6-luna')
    args = parser.parse_args()
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(ROOT / '.env')
    if not os.getenv('OPENAI_API_KEY') or not os.getenv('DATABASE_URL'):
        raise SystemExit('Thiếu OPENAI_API_KEY hoặc DATABASE_URL trong .env')
    question = args.question or input('Nhập câu hỏi: ').strip()
    if not question:
        raise SystemExit('Câu hỏi không được để trống')
    sys.path.insert(0, str(ROOT / 'starter'))
    from starter.day6_backend.embeddings import MyEmbedder
    from starter.day6_backend.store import PgVectorStore
    from starter.agentic import run_agent

    print('Đang tải model embedding và tìm bằng chứng...', flush=True)
    embedder = MyEmbedder('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    retriever = DenseRetriever(embedder, PgVectorStore(os.environ['DATABASE_URL'], embedder.dimensions))
    controller = OpenAIController(OpenAI(), args.model)
    result = run_agent(question, controller, retriever, max_searches=3, top_k=3, budget=2000)
    result.update(question=question, model=args.model, usage=controller.usage)
    out = ROOT / 'starter' / 'results' / 'agent-demo'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'trace.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for event in result['events']:
        if event['event'] == 'search':
            print('\nTruy vấn:', event['query'])
            for chunk in event['results']:
                print(f"  {chunk['id']} | trang {chunk['page']} | score {chunk['score']:.4f}")
    print('\nTrạng thái:', result['status'])
    print('Trả lời:', result['answer'])
    print('Trace:', out / 'trace.json')


if __name__ == '__main__':
    main()
