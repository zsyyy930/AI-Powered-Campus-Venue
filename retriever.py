"""场馆知识检索：P2 向量语义检索（无索引时回退关键词）"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

try:
    import config
except ImportError:

    class config:  # type: ignore
        KNOWLEDGE_DIR = "knowledge"
        DATA_DIR = "data"
        CHUNKS_FILE = "chunks.json"
        EMBEDDINGS_FILE = "embeddings.npz"
        TOP_K = 5
        SIMILARITY_THRESHOLD = 0.35
        USE_VECTOR_INDEX = True


def _data_dir() -> Path:
    return Path(getattr(config, "DATA_DIR", "data"))


def load_chunks() -> list[dict]:
    path = _data_dir() / getattr(config, "CHUNKS_FILE", "chunks.json")
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_embeddings() -> tuple[np.ndarray, list[str]] | None:
    path = _data_dir() / getattr(config, "EMBEDDINGS_FILE", "embeddings.npz")
    if not path.exists():
        return None
    data = np.load(path, allow_pickle=False)
    return data["embeddings"], list(data["ids"])


def load_knowledge() -> list[dict]:
    """兼容旧接口：无索引时按文件加载。"""
    root = Path(config.KNOWLEDGE_DIR)
    if not root.exists():
        return []
    items: list[dict] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            items.append({"name": path.stem, "content": text, "source": path.name})
    return items


def _normalize_hit(chunk: dict, score: float | None = None) -> dict:
    hit = {
        "id": chunk.get("id", ""),
        "source": chunk.get("source", ""),
        "title": chunk.get("title", ""),
        "text": chunk.get("text", chunk.get("content", "")),
        "name": chunk.get("title") or Path(chunk.get("source", "")).stem,
        "content": chunk.get("text", chunk.get("content", "")),
    }
    if score is not None:
        hit["score"] = round(float(score), 4)
    return hit


def _retrieve_vector(query: str, top_k: int) -> list[dict]:
    from embedder import embed_query

    chunks = load_chunks()
    emb_data = load_embeddings()
    if not chunks or emb_data is None:
        return []

    matrix, ids = emb_data
    id_to_chunk = {c["id"]: c for c in chunks}
    q_vec = embed_query(query)
    scores = matrix @ q_vec

    threshold = getattr(config, "SIMILARITY_THRESHOLD", 0.35)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    hits: list[dict] = []
    for idx, score in ranked:
        if score < threshold:
            break
        cid = ids[idx]
        chunk = id_to_chunk.get(cid)
        if chunk:
            hits.append(_normalize_hit(chunk, score))
        if len(hits) >= top_k:
            break
    return hits


def _retrieve_keyword(query: str, top_k: int) -> list[dict]:
    chunks = load_chunks()
    if chunks:
        q = query.lower()
        scored: list[tuple[int, dict]] = []
        for c in chunks:
            text = c.get("text", "").lower()
            score = sum(1 for token in q.split() if token and token in text)
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [_normalize_hit(c, s) for s, c in scored[:top_k]]

    docs = load_knowledge()
    q = query.lower()
    scored: list[tuple[int, dict]] = []
    for doc in docs:
        content = doc["content"].lower()
        score = sum(1 for token in q.split() if token and token in content)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [_normalize_hit(d, s) for s, d in scored[:top_k]]


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    k = top_k or getattr(config, "TOP_K", 5)
    use_vector = getattr(config, "USE_VECTOR_INDEX", True)
    if use_vector and load_chunks() and load_embeddings() is not None:
        return _retrieve_vector(query, k)
    return _retrieve_keyword(query, k)
