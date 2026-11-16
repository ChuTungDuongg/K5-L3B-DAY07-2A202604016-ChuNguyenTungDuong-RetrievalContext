import json
import sys
from pathlib import Path

# Import baseline có sẵn trong starter.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "starter"))

from baseline import TfidfIndex

chunks_path = ROOT / "starter" / "data" / "day6-A" / "chunks.json"
chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

print(f"Đã tải {len(chunks)} chunk.")
index = TfidfIndex(chunks)

question = input("\nNhập câu hỏi: ").strip()
if not question:
    raise ValueError("Bạn chưa nhập câu hỏi.")

results = index.search(question, top_k=3)

if not results:
    print("\nKhông tìm thấy kết quả khớp từ khóa.")

for rank, chunk in enumerate(results, start=1):
    print(f"\n--- Kết quả {rank} ---")
    print(f"ID: {chunk['id']}")
    print(f"Nguồn: {chunk['source']}")
    print(f"Trang: {chunk['page']}")
    print(f"Điểm TF-IDF: {chunk['score']:.4f}")
    print(f"Nội dung:\n{chunk['text']}")