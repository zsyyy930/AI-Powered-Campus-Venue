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


def _chunks_grouped_by_source() -> dict[str, list[dict]]:
    """索引中同一 md 的全部 chunk，按 id 顺序排列。"""
    grouped: dict[str, list[dict]] = {}
    for c in load_chunks():
        src = c.get("source", "")
        if not src:
            continue
        grouped.setdefault(src, []).append(c)
    for parts in grouped.values():
        parts.sort(key=lambda x: x.get("id", ""))
    return grouped


def merge_hits_by_source(hits: list[dict], max_sources: int | None = None) -> list[dict]:
    """
    按 source（md 文件）合并检索结果：
    - 同一文件在 top 池里出现过的，将其在索引中的全部 ## chunk 拼成一条；
    - 保留该文件最高相似度作为排序依据。
    """
    if not hits:
        return []

    max_sources = max_sources or getattr(config, "MAX_VENUES_IN_PROMPT", 3)
    all_by_source = _chunks_grouped_by_source()

    source_order: list[str] = []
    best_score: dict[str, float] = {}
    for h in hits:
        src = h.get("source", "")
        if not src:
            continue
        score = float(h.get("score", 0) or 0)
        if src not in best_score:
            source_order.append(src)
            best_score[src] = score
        else:
            best_score[src] = max(best_score[src], score)

    merged: list[dict] = []
    for src in source_order[:max_sources]:
        parts = all_by_source.get(src)
        if parts:
            text = "\n\n".join(p.get("text", "") for p in parts)
        else:
            same = [h for h in hits if h.get("source") == src]
            text = "\n\n".join(h.get("text", "") for h in same)
        stem = Path(src).stem
        merged.append(
            {
                "source": src,
                "title": stem,
                "name": stem,
                "text": text,
                "content": text,
                "score": round(best_score[src], 4),
            }
        )
    return merged


def retrieve_for_prompt(query: str, max_sources: int | None = None) -> list[dict]:
    """检索供 Prompt 使用：先扩大 chunk 池，再按 md 文件合并为完整条目。"""
    pool = getattr(config, "RETRIEVE_POOL_SIZE", None)
    if pool is None:
        pool = max(getattr(config, "TOP_K", 5) * 4, 20)
    hits = retrieve(query, top_k=pool)
    return merge_hits_by_source(hits, max_sources)


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
    
    # 先按场馆分组，计算每个场馆的最高分数和是否免费
    venue_scores: dict[str, tuple[float, bool]] = {}
    for idx, score in enumerate(scores):
        cid = ids[idx]
        chunk = id_to_chunk.get(cid)
        if chunk:
            source = chunk.get("source", "")
            text = chunk.get("text", "")
            is_free = "免费" in text
            if source not in venue_scores or score > venue_scores[source][0]:
                venue_scores[source] = (score, is_free)
    
    # 按综合分数排序场馆：相似度分数 + 免费奖励
    ranked_venues = sorted(
        venue_scores.items(),
        key=lambda x: x[1][0] + (0.05 if x[1][1] else 0),
        reverse=True
    )

    hits: list[dict] = []
    collected_sources: set[str] = set()
    
    for source, (score, is_free) in ranked_venues[:top_k * 2]:
        if score < threshold and len(hits) > 0:
            break
        collected_sources.add(source)
        # 添加同一文件的所有段落
        for c in chunks:
            if c.get("source") == source:
                hits.append(_normalize_hit(c, score))
        if len(hits) >= top_k * 3:
            break
    return hits[:top_k * 3]


def _simple_tokenize(text: str) -> list[str]:
    """简单的中文分词：按常见词分割"""
    # 按长度从长到短排序，优先匹配长词
    common_words = sorted([
        '五人制', '七人制', '十一人制',
        '羽毛球场', '篮球场', '足球场', '排球场', '网球场', '游泳馆', '健身房',
        '田径场', '风雨操场', '灯光球场', '气膜馆',
        '个人', '我们', '你们', '他们', '它们', '一起', '想去', '想要', '需要',
        '可以', '不能', '不要', '没有', '有', '是', '的', '了', '在', '和', '与', '或',
        '以及', '还是', '但是', '不过', '因为', '所以', '如果', '适合', '推荐', '附近',
        # 收费相关词汇
        '收费', '免费', '价格', '费用', '多少钱', '票价', '校园卡', '刷校园卡',
        # 疑问词
        '怎么', '如何', '为什么', '哪里', '什么', '吗', '呢', '吧', '啊',
        # 运动项目单字（确保能正确分词）
        '篮球', '足球', '排球', '羽毛球', '乒乓球', '网球', '游泳', '健身', '跑步', '田径',
        # 散步相关词汇
        '散步', '慢跑', '慢走', '走走', '校园散步', '饭后散步',
        # 单字常见词
        '我', '你', '他', '她', '它', '要', '能', '会', '想', '去', '来', '做', '看', '听', '说', '问', '答', '找', '给', '拿', '放', '走', '跑', '跳', '打'
    ], key=lambda x: -len(x))
    
    tokens = []
    i = 0
    while i < len(text):
        matched = False
        # 尝试匹配常见词（按长度从长到短）
        for word in common_words:
            if text[i:i+len(word)] == word:
                tokens.append(word)
                i += len(word)
                matched = True
                break
        if not matched:
            # 尝试匹配运动项目单字
            sport_chars = {'足', '篮', '排', '网', '羽', '游', '健', '跑', '田'}
            if text[i] in sport_chars and i + 1 < len(text):
                tokens.append(text[i:i+2])
                i += 2
            # 尝试匹配双字词
            elif i + 1 < len(text):
                tokens.append(text[i:i+2])
                i += 2
            else:
                tokens.append(text[i])
                i += 1
    return tokens

def _retrieve_keyword(query: str, top_k: int) -> list[dict]:
    # 运动项目同义词映射
    sport_synonyms = {
        '踢球': ['足球', '足球场', '五人制', '五人'],
        '足球': ['足球', '足球场', '五人制', '五人'],
        '五人': ['五人制', '足球场', '足球'],
        '五个': ['五人制', '五人'],
        '羽毛球': ['羽毛球', '羽毛球场'],
        '篮球': ['篮球', '篮球场', '室内篮球'],
        '室内篮球': ['室内', '篮球场', '风雨操场'],
        '室内': ['风雨操场', '室内', '体育馆'],
        '排球': ['排球', '排球场'],
        '网球': ['网球', '网球场'],
        '游泳': ['游泳', '游泳馆'],
        '健身': ['健身', '健身房'],
        '跑步': ['跑步', '田径'],
        '田径': ['田径', '跑步'],
        # 收费相关词汇
        '收费': ['收费', '免费', '价格', '费用', '多少钱', '价格', '票价', '办卡', '卡类', '单次'],
        '免费': ['免费', '收费', '价格', '费用', '刷校园卡', '免费进入', '不想花钱', '不花钱', '省钱'],
        '多少钱': ['收费', '免费', '价格', '费用', '多少钱'],
        # 免费相关词汇（否定形式）
        '不想花钱': ['免费', '不收费', '免费进入'],
        '不花钱': ['免费', '不收费', '免费进入'],
        '省钱': ['免费', '不收费'],
        # 单字否定词
        '不': ['免费', '不收费', '无需'],
        '想': ['想要', '需要'],
        '花': ['花钱', '费用', '收费'],
        '钱': ['费用', '收费', '价格', '免费'],
        # 办卡相关词汇
        '办卡': ['办卡', '卡类', '月卡', '年卡', '半年卡', '单次'],
        '卡类': ['卡类', '办卡', '月卡', '年卡', '半年卡', '单次'],
        # 入场方式相关词汇
        '怎么进': ['刷校园卡', '进入', '入场', '进入方式', '门禁'],
        '进入': ['刷校园卡', '进入', '入场', '门禁'],
        '校园卡': ['刷校园卡', '校园卡', '免费进入'],
        # 散步相关词汇
        '散步': ['散步', '慢跑', '慢走', '田径', '田径场'],
        '慢跑': ['慢跑', '散步', '慢走', '田径', '田径场'],
        '慢走': ['慢走', '散步', '慢跑', '田径', '田径场'],
        '走': ['散步', '慢跑', '慢走', '田径', '田径场'],
    }
    
    chunks = load_chunks()
    if chunks:
        q = query.lower()
        scored: list[tuple[int, dict]] = []
        q_tokens = _simple_tokenize(q)
        
        for c in chunks:
            text = c.get("text", "").lower()
            score = 0
            is_free = '免费' in text
            for token in q_tokens:
                if not token:
                    continue
                # 完全匹配
                if token in text:
                    score += 3
                # 运动项目同义词匹配
                elif token in sport_synonyms:
                    for synonym in sport_synonyms[token]:
                        if synonym in text:
                            score += 2.5
                            break
                # 单字匹配
                elif len(token) == 1:
                    if token in text:
                        score += 0.5
            # 如果查询中包含免费相关词汇，对免费场馆给予额外分数加成
            free_query_tokens = {'免费', '不花钱', '不想花钱', '省钱', '免费进入'}
            has_free_intent = any(t in q_tokens for t in free_query_tokens)
            # 检测"不"+"花钱"模式
            if '不' in q_tokens and ('花钱' in q_tokens or '钱' in q_tokens):
                has_free_intent = True
            # 检测"不想花钱"模式
            if '不想' in q_tokens and ('花钱' in q_tokens or '钱' in q_tokens):
                has_free_intent = True
            # 检测"们不"+"想"+"花钱"模式（处理分词错误）
            if '们不' in q_tokens and ('想' in q_tokens or '要' in q_tokens) and ('花钱' in q_tokens or '钱' in q_tokens):
                has_free_intent = True
            # 使用原始查询字符串检测
            if '不想花钱' in q or '不想花錢' in q:
                has_free_intent = True
            if '不想' in q and ('花钱' in q or '钱' in q):
                has_free_intent = True
            if is_free and has_free_intent:
                score += 5  # 免费场馆加分
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [_normalize_hit(c, s) for s, c in scored[:top_k]]

    docs = load_knowledge()
    q = query.lower()
    scored: list[tuple[int, dict]] = []
    q_tokens = _simple_tokenize(q)
    
    for doc in docs:
        content = doc["content"].lower()
        score = 0
        for token in q_tokens:
            if not token:
                continue
            if token in content:
                score += 3
            elif token in sport_synonyms:
                for synonym in sport_synonyms[token]:
                    if synonym in content:
                        score += 2.5
                        break
            elif len(token) == 1:
                if token in content:
                    score += 0.5
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [_normalize_hit(d, s) for s, d in scored[:top_k]]


def _normalize_query(query: str) -> str:
    """将数字转换为中文，提高匹配效果"""
    num_map = {
        '1': '一', '2': '二', '3': '三', '4': '四', '5': '五',
        '6': '六', '7': '七', '8': '八', '9': '九', '0': '零',
        '10': '十', '11': '十一', '12': '十二', '13': '十三',
        '14': '十四', '15': '十五', '20': '二十', '30': '三十',
        '50': '五十', '100': '一百'
    }
    result = query
    for num, char in num_map.items():
        result = result.replace(num, char)
    return result

def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    k = top_k or getattr(config, "TOP_K", 5)
    use_vector = getattr(config, "USE_VECTOR_INDEX", True)
    # 添加数字到中文的转换
    normalized_query = _normalize_query(query)
    
    # 检测查询是否包含免费相关意图
    q_tokens = _simple_tokenize(normalized_query)
    free_query_tokens = {'免费', '不花钱', '不想花钱', '省钱', '免费进入'}
    has_free_intent = any(t in q_tokens for t in free_query_tokens)
    # 检测各种否定模式
    if '不' in q_tokens and ('花钱' in q_tokens or '钱' in q_tokens):
        has_free_intent = True
    if '不想' in q_tokens and ('花钱' in q_tokens or '钱' in q_tokens):
        has_free_intent = True
    if '们不' in q_tokens and ('想' in q_tokens or '要' in q_tokens) and ('花钱' in q_tokens or '钱' in q_tokens):
        has_free_intent = True
    # 检测"不想"后面跟"花钱"的模式
    q_str = normalized_query
    if '不想花钱' in q_str or '不想花錢' in q_str:
        has_free_intent = True
    if '不想' in q_str and ('花钱' in q_str or '钱' in q_str):
        has_free_intent = True
    
    # 始终同时运行关键词检索，确保不遗漏重要结果
    keyword_results = _retrieve_keyword(normalized_query, k)
    
    if use_vector and load_chunks() and load_embeddings() is not None:
        vector_results = _retrieve_vector(normalized_query, k)
        
        # 合并策略：按场馆分组，确保每个场馆至少有一个结果被保留
        # 先收集所有来源
        all_results = vector_results + keyword_results
        
        # 如果用户明确表示想要免费场馆，过滤掉收费场馆
        if has_free_intent:
            all_results = [r for r in all_results if '免费' in r.get('text', '')]
        
        # 按来源分组，保留每个来源的所有chunks
        venues: dict[str, list[dict]] = {}
        for r in all_results:
            src = r.get('source', '')
            if src not in venues:
                venues[src] = []
            venues[src].append(r)
        
        # 按分数排序场馆（取每个场馆的最高分数）
        ranked_venues = sorted(
            venues.items(),
            key=lambda x: max(r.get('score', 0) for r in x[1]),
            reverse=True
        )
        
        # 合并结果，每个场馆最多保留3个chunks，确保所有场馆都能被包含
        merged = []
        for src, chunks in ranked_venues[:k]:
            # 对每个场馆的chunks按分数排序，取前3个
            sorted_chunks = sorted(chunks, key=lambda x: x.get('score', 0), reverse=True)
            merged.extend(sorted_chunks[:3])
        
        return merged[:k * 3]
    
    return keyword_results
