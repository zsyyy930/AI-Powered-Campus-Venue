"""程序入口：多轮对话 + RAG + 边界处理（P3）"""

from conversation import Conversation
from embedder import warmup
from llm import LLMError


def main() -> None:
    warmup()
    conv = Conversation()
    print("校园智能场馆匹配平台（P3 多轮 + 边界）")
    print("命令：quit 退出 | reset 清空对话历史\n")

    while True:
        query = input("你：").strip()
        if not query:
            continue
        low = query.lower()
        if low in {"quit", "exit", "q"}:
            print("再见。")
            break
        if low == "reset":
            conv.reset()
            print("（已清空对话历史，开始新会话）\n")
            continue

        print("\n助手：", end="")
        try:
            print(conv.turn(query))
        except LLMError as e:
            print(f"[错误] {e}")
        print(f"\n（本轮结束，已进行 {conv.turn_count} 轮有记录的对话）")
        print("-" * 40 + "\n")


if __name__ == "__main__":
    main()
