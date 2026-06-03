"""P0 自检：仅测试 DeepSeek 能否连通（不跑检索、不跑 main）"""

from llm import LLMError, chat


def main() -> None:
    print("=== DeepSeek 连通测试 ===\n")
    messages = [
        {"role": "system", "content": "你是校园场馆助手，用一句话回答。"},
        {"role": "user", "content": "用一句话说明：什么是校园场馆智能匹配？"},
    ]
    try:
        answer = chat(messages)
        print("调用成功，模型回复：\n")
        print(answer)
        print("\n=== 测试通过，可继续运行 python main.py ===")
    except LLMError as e:
        print("调用失败：", e)
        print("\n请检查：")
        print("  1. 是否已创建 config.py 并填写 API_KEY")
        print("  2. API_BASE 是否为 https://api.deepseek.com")
        print("  3. 本机能否访问外网")


if __name__ == "__main__":
    main()
