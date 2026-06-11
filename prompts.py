"""Prompt 模板与边界判断（P3）"""

from __future__ import annotations

import re

try:
    import config
except ImportError:

    class config:  # type: ignore
        MAX_VENUES_IN_PROMPT = 3


SYSTEM_PROMPT = """你是「校园智能场馆匹配助手」，只回答与本校体育场馆、活动场地、预约与使用相关的问题。

【必须遵守】
1. 仅根据用户消息中「参考资料」部分作答；不得编造场馆名称、开放时间、电话、费用等未在参考资料中出现的信息。
2. 若标注为「知识库无相关条目」，须明确说明资料中未记载，可建议用户联系体育部或场馆管理中心核实；不要假装检索到了内容。
3. 若用户问题与场馆/活动场地无关（如教务、成绩、选课、转专业、宿舍管理等），礼貌说明本助手只做场馆匹配，并建议咨询相应部门。
4. 多轮对话时，结合上文理解指代（如「第二个」「它」），仍须遵守第 1–3 条。
5. 语气简洁、有条理；推荐时说明理由（容量、位置、设备等）。
6. 【引用标注】回答中每个具体信息（如时间、地点、电话、价格）后面，必须用 [来源: 文件名] 标注。示例：休闲餐厅早餐 06:30-09:00 [来源: 东区大食堂.md]。同一信息来自多个来源时，全部标注。
7. 【合并来源】如果连续多条信息来自同一个文件的同一个段落，只在最后合并标注一次。"""

OUT_OF_SCOPE_REPLY = """您的问题似乎不属于「校园场馆/活动场地」范围，本助手无法根据场馆知识库准确回答。

我主要负责：场馆推荐、容量与设备、开放时间与预约方式等。

教务、成绩、选课、转专业等问题请咨询教务处；如需场馆帮助，请直接描述活动类型、人数与时间。"""


NO_CONTEXT_USER_WRAPPER = """用户需求：{query}

【知识库检索结果】未找到与问题足够相关的参考资料（请勿编造任何场馆信息）。

请按系统要求：说明资料未记载，列出可向用户确认的关键信息（人数、室内/室外、时间段），并建议通过学校官方场馆预约渠道查询。"""


# 明显非场馆领域的关键词（可按本校情况增删）
_OUT_OF_SCOPE_PATTERNS = [
    r"转专业|绩点|gpa|学分|选课|退课|补考|挂科|期末考试安排",
    r"教务处|教务系统|成绩单|学位证|毕业要求",
    r"宿舍分配|换宿舍|学费|奖学金",
    r"数学题|编程作业|写代码|bug",
]


def is_out_of_scope(query: str) -> bool:
    """规则预判：明显非场馆话题时直接拒答，节省 API 并强化边界。"""
    q = query.strip().lower()
    if not q:
        return False
    for pat in _OUT_OF_SCOPE_PATTERNS:
        if re.search(pat, q, re.IGNORECASE):
            return True
    return False


def build_retrieval_query(current: str, raw_history: list[tuple[str, str]]) -> str:
    """多轮时把上一轮摘要拼进检索 query，便于理解「第二个」「那个馆」。"""
    current = current.strip()
    if not raw_history:
        return current
    last_user, _ = raw_history[-1]
    return (
        f"上一轮用户问题：{last_user}\n"
        f"本轮追问：{current}"
    )


def build_rag_user_message(query: str, chunks: list[dict]) -> str:
    """将检索结果拼入本轮 user 消息（写入对话 history）。"""
    if not chunks:
        return NO_CONTEXT_USER_WRAPPER.format(query=query)

    max_n = getattr(config, "MAX_VENUES_IN_PROMPT", 3)
    blocks = []
    for i, c in enumerate(chunks[:max_n], 1):
        src = c.get("source", "未知文件")
        start = c.get("start_line", "?")
        end = c.get("end_line", "?")
        blocks.append(
            f"### 参考资料 [{i}] (来源: {src}:{start}-{end})\n"
            f"{c.get('text', c.get('content', ''))}\n"
    max_n = getattr(config, "MAX_VENUES_IN_PROMPT", 5)
    
    # 按来源文件分组，保留排序顺序
    venues: dict[str, list[dict]] = {}
    seen_sources: list[str] = []  # 保持顺序
    
    for c in chunks:
        src = c.get("source", "")
        if src not in venues:
            venues[src] = []
            seen_sources.append(src)
        venues[src].append(c)
    
    blocks = []
    # 使用 seen_sources 保持原有的排序顺序
    for i, src in enumerate(seen_sources[:max_n], 1):
        venue_chunks = venues[src]
        # 合并同一个场馆的所有内容
        content_parts = []
        for c in venue_chunks:
            title = c.get("title", "")
            text = c.get("text", c.get("content", ""))
            content_parts.append(f"## {title}\n{text}")
        
        first_chunk = venue_chunks[0]
        score = first_chunk.get("score")
        extra = f"（相似度 {score}）" if score is not None else ""
        title = c.get("title", c.get("name", ""))
        if title.startswith("自习-"):
            title = title[len("自习-") :]
        blocks.append(
            f"### 参考资料 {i}：{title} {extra}\n"
            f"来源文件：{src}\n{c.get('text', c.get('content', ''))}"
        )
    
    refs = "\n\n".join(blocks)
    return f"用户需求: {query}\n\n【知识库参考资料】\n{refs}\n\n请根据以上参考资料回答，并在每个具体信息后标注 [来源: 文件名:行号-行号]。"