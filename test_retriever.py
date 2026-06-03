"""P0 自检：测试知识库能否被加载、关键词检索是否有结果"""

from retriever import load_knowledge, retrieve


def main() -> None:
    print("=== 知识库与检索测试 ===\n")
    docs = load_knowledge()
    print(f"共加载 {len(docs)} 个场馆文件：")
    for d in docs:
        print(f"  - {d['name']}（约 {len(d['content'])} 字）")

    if not docs:
        print("\n知识库为空，请在 knowledge/ 下添加 .md 文件。")
        return

    query = "羽毛球"
    print(f"\n测试检索，查询词：「{query}」")
    hits = retrieve(query)
    print(f"命中 {len(hits)} 条：")
    for h in hits:
        preview = h["content"][:80].replace("\n", " ")
        print(f"  - {h['name']}: {preview}...")


if __name__ == "__main__":
    main()
