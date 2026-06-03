"""场馆知识检索与粗匹配"""

from pathlib import Path

try:
    import config
except ImportError:
    # P0 自检：尚未创建 config.py 时使用默认值（仅检索，不调 API）
    class config:  # type: ignore
        KNOWLEDGE_DIR = "knowledge"
        TOP_K = 5


def load_knowledge() -> list[dict]:
    """从 knowledge/ 目录加载场馆文档，返回 [{name, content}, ...]"""
    root = Path(config.KNOWLEDGE_DIR)
    if not root.exists():
        return []

    items: list[dict] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            items.append({"name": path.stem, "content": text})
    return items


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    """
    根据用户查询做简单关键词检索，返回最相关的场馆条目。
    后续可替换为向量检索 / 重排序等方案。
    """
    k = top_k or config.TOP_K
    docs = load_knowledge()
    if not docs:
        return []

    q = query.lower()
    scored: list[tuple[int, dict]] = []
    for doc in docs:
        content = doc["content"].lower()
        score = sum(1 for token in q.split() if token and token in content)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:k]]
