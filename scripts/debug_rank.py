import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retriever import retrieve, retrieve_for_prompt

q1 = "我想要去离食堂近一点的地方自习，要有插座"
q2 = "那文韵丹青咖啡店呢"

print("=== Q1 raw top 20 ===")
raw = retrieve(q1, top_k=20)
for i, h in enumerate(raw, 1):
    mark = " <--" if "文韵丹青" in h["source"] else ""
    print(f"  {i:2}. {h.get('score'):.4f} {h['source']} | {h['title']}{mark}")

print("\n=== Q1 merged (MAX_VENUES=3) ===")
for m in retrieve_for_prompt(q1):
    print(f"  {m.get('score'):.4f} {m['source']}")

print("\n=== Q2 merged ===")
for m in retrieve_for_prompt(q2):
    print(f"  {m.get('score'):.4f} {m['source']}")
