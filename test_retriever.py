"""自检：知识库文档数量与检索"""

from pathlib import Path

import config
from retriever import load_chunks, retrieve


def count_venue_files() -> int:
    return len(list(Path(config.KNOWLEDGE_DIR).glob("*.md")))


def main() -> None:
    print("=== 知识库与检索测试（P1/P2）===\n")

    md_count = count_venue_files()
    print(f"场馆文档（knowledge/*.md）：{md_count} 个")
    if md_count < 15:
        print(f"  提示：任务书要求 ≥15 个类似「示例-体育馆.md」的独立文档，当前差 {15 - md_count} 个。")

    chunks = load_chunks()
    if chunks:
        print(f"检索索引切块：{len(chunks)} 段（由上述文档按 ## 标题切分，用于向量/关键词检索）")
        for c in chunks[:3]:
            print(f"  - [{c['id']}] {c['title'][:30]}...")
        if len(chunks) > 3:
            print(f"  ...")
    else:
        print("未找到 data/chunks.json，请先运行: python indexer.py --rebuild")

    for query in ("羽毛球", "游泳"):
        print(f"\n查询：「{query}」")
        hits = retrieve(query)
        if not hits:
            print("  （无命中，可调低 config.py 中 SIMILARITY_THRESHOLD）")
            continue
        for h in hits:
            sc = h.get("score", "-")
            preview = h["text"][:60].replace("\n", " ")
            print(f"  - {h['title']} score={sc} | {preview}...")
