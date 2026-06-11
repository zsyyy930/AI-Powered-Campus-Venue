"""自检：知识库文档数量与检索"""

from pathlib import Path

import config
from retriever import load_chunks, merge_hits_by_source, retrieve, retrieve_for_prompt


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

    print("\n--- 按 source 合并（Prompt 用）---")
    merged = retrieve_for_prompt("文韵丹青咖啡店怎么样")
    assert merged, "应有命中"
    top = merged[0]
    assert "插座" in top["text"], "合并后应含插座字段"
    assert "距食堂" in top["text"], "合并后应含距食堂字段"
    print(f"  文韵丹青合并后字段完整：{top['source']}")
    print(f"  Prompt 条数：{len(merged)}")
