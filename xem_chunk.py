import json
from pathlib import Path

path = Path("starter/data/day6-A/chunks.json")
chunks = json.loads(path.read_text(encoding="utf-8"))

page = int(input("Nhập số trang PDF muốn xem: "))

for chunk in chunks:
    if chunk["page"] == page:
        print(f"\n--- {chunk['id']} ---")
        print(chunk["text"])