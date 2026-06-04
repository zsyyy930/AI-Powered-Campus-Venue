"""P3 自检：边界规则与 Prompt 拼装（不调用 DeepSeek）"""

from conversation import Conversation
from prompts import build_rag_user_message, build_retrieval_query, is_out_of_scope
from retriever import retrieve


def main() -> None:
    print("=== P3 边界与多轮（离线部分）===\n")

    cases = [
        ("约 50 人打羽毛球，要室内", False),
        ("怎么申请转专业", True),
        ("绩点怎么算", True),
    ]
    for q, expect_oos in cases:
        got = is_out_of_scope(q)
        ok = "✓" if got == expect_oos else "✗"
        print(f"{ok} 边界预判 「{q}」 -> out_of_scope={got} (期望 {expect_oos})")

    print("\n--- 检索 query 多轮改写 ---")
    hist = [("东区有哪些场馆可以打球？", "推荐了体育馆...")]
    q2 = "第二个怎么预约？"
    rq = build_retrieval_query(q2, hist)
    print(rq)

    print("\n--- 无检索命中时的 user 消息（应要求不编造）---")
    msg = build_rag_user_message("火星上的体育馆", [])
    print(msg[:200], "...\n")

    print("--- 有检索命中（假数据/示例库）---")
    print("（首次会加载 embedding 模型，约 30 秒～2 分钟，请稍候…）")
    hits = retrieve("羽毛球")
    print(f"命中 {len(hits)} 条")
    if hits:
        print(build_rag_user_message("羽毛球", hits)[:300], "...")

    print("\n--- Conversation 状态 ---")
    c = Conversation()
    assert c.turn_count == 0
    c.reset()
    assert c.turn_count == 0
    print("Conversation 初始化/reset 正常")

    print("\n完整多轮 + DeepSeek 请运行: python main.py")
    print("建议试：先问场馆 -> 追问「第二个」-> 问转专业（应边界拒答）")


if __name__ == "__main__":
    main()
