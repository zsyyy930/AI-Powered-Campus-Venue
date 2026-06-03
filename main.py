"""程序入口：校园智能场馆匹配（P0：单轮 + 关键词检索 + DeepSeek）"""

import config
from llm import LLMError, chat
from retriever import retrieve


SYSTEM_PROMPT = """你是校园场馆匹配助手。根据用户需求与检索到的场馆资料，
推荐最合适的场馆，并简要说明理由（容量、位置、设备、预约方式等）。
若资料不足，请明确说明并给出补充信息建议。"""


def build_user_message(query: str, venues: list[dict]) -> str:
    if not venues:
        return f"用户需求：{query}\n\n（知识库中暂无匹配场馆资料，请根据常识给出建议并提示补充 knowledge/ 数据。）"

    blocks = []
    for i, v in enumerate(venues[: config.MAX_VENUES_IN_PROMPT], 1):
        blocks.append(f"### 候选场馆 {i}：{v['name']}\n{v['content']}")
    context = "\n\n".join(blocks)
    return f"用户需求：{query}\n\n检索到的场馆资料：\n{context}"


def match_venues(query: str) -> str:
    venues = retrieve(query)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(query, venues)},
    ]
    return chat(messages)


def main() -> None:
    print("校园智能场馆匹配平台（输入 quit 退出）\n")
    while True:
        query = input("请描述您的活动需求：").strip()
        if not query:
            continue
        if query.lower() in {"quit", "exit", "q"}:
            print("再见。")
            break
        print("\n正在匹配...\n")
        try:
            print(match_venues(query))
        except LLMError as e:
            print(f"[错误] {e}")
        print("\n" + "-" * 40 + "\n")


if __name__ == "__main__":
    main()
