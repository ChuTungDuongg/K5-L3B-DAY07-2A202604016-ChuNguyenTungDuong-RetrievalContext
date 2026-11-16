import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent

sys.path.insert(0, str(ROOT / "starter"))

from starter.day6_backend.embeddings import MyEmbedder
from starter.day6_backend.store import PgVectorStore
from baseline import TfidfIndex


def reciprocal_rank_fusion(dense_results, lexical_results, rrf_k=60):
    """Gộp kết quả theo ID, dựa trên thứ hạng của từng phương pháp."""
    combined = {}

    for method, results in (
        ("dense", dense_results),
        ("tfidf", lexical_results),
    ):
        for rank, chunk in enumerate(results, start=1):
            # Kết quả Day 6 dùng chunk_id; TF-IDF dùng id.
            chunk_id = chunk.get("id") or chunk["chunk_id"]

            if chunk_id not in combined:
                combined[chunk_id] = {
                    "id": chunk_id,
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "score": 0.0,
                    "ranks": {},
                }

            combined[chunk_id]["score"] += 1 / (rrf_k + rank)
            combined[chunk_id]["ranks"][method] = rank

    return sorted(
        combined.values(),
        key=lambda chunk: (-chunk["score"], chunk["id"]),
    )


load_dotenv(ROOT / ".env")

chunks_path = ROOT / "starter" / "data" / "day6-A" / "chunks.json"
chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
lexical_index = TfidfIndex(chunks)

print("Đang tải model embedding...")
embedder = MyEmbedder(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
store = PgVectorStore(
    database_url=os.getenv("DATABASE_URL"),
    dimensions=embedder.dimensions,
)

question = input("\nNhập câu hỏi: ").strip()
if not question:
    raise ValueError("Bạn chưa nhập câu hỏi.")

# Lấy 10 ứng viên từ mỗi phương pháp trước khi hợp nhất.
dense_results = store.search(
    strategy="A",
    query_vector=embedder.embed_query(question),
    top_k=10,
)
lexical_results = lexical_index.search(question, top_k=10)

results = reciprocal_rank_fusion(dense_results, lexical_results)[:3]

for rank, chunk in enumerate(results, start=1):
    print(f"\n--- Kết quả hybrid {rank} ---")
    print(f"ID: {chunk['id']}")
    print(f"Nguồn: {chunk['source']}")
    print(f"Trang: {chunk['page']}")
    print(f"Điểm RRF: {chunk['score']:.4f}")
    print(f"Thứ hạng ban đầu: {chunk['ranks']}")
    print(f"Nội dung:\n{chunk['text']}")