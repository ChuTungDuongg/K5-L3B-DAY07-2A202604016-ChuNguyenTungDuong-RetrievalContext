import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Cho phép dùng lại code embedding và database của Day 6.


from starter.day6_backend.embeddings import MyEmbedder
from starter.day6_backend.store import PgVectorStore

# Đọc cấu hình database từ .env của Day 7.
load_dotenv(Path(__file__).resolve().parent / ".env")

database_url = os.getenv("DATABASE_URL")
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print("Đang tải model embedding...")
embedder = MyEmbedder(model_name)

store = PgVectorStore(
    database_url=database_url,
    dimensions=embedder.dimensions,
)

question = input("\nNhập câu hỏi: ").strip()
if not question:
    raise ValueError("Bạn chưa nhập câu hỏi.")

print("\nĐang tìm trong database...")
query_vector = embedder.embed_query(question)

results = store.search(
    strategy="A",
    query_vector=query_vector,
    top_k=3,
)

for rank, chunk in enumerate(results, start=1):
    print(f"\n--- Kết quả {rank} ---")
    print(f"ID: {chunk['chunk_id']}")
    print(f"Nguồn: {chunk['source']}")
    print(f"Trang: {chunk['page']}")
    print(f"Điểm tương đồng: {chunk['score']:.4f}")
    print(f"Nội dung:\n{chunk['text']}")