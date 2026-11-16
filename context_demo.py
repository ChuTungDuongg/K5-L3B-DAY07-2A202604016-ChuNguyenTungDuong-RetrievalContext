import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "starter"))

from baseline import TfidfIndex, hit, pack_context

chunks = json.loads(
    (ROOT / "starter/data/day6-A/chunks.json").read_text(encoding="utf-8")
)
questions = json.loads(
    (ROOT / "starter/data/day6-A/questions-dev.json").read_text(encoding="utf-8")
)

case = questions[0]
results = TfidfIndex(chunks).search(case["question"], top_k=3)

for budget in (800, 2000):
    context, ids = pack_context(results, budget=budget)
    selected = [chunk for chunk in results if chunk["id"] in ids]
    has_evidence = any(hit(chunk, case["gold"]) for chunk in selected)

    print(f"\n--- Budget: {budget} ký tự ---")
    print(f"Context thực tế: {len(context)} ký tự")
    print(f"Có gold trong context: {has_evidence}")
    print("Các chunk được giữ:")
    for chunk_id in ids:
        print(" ", chunk_id)