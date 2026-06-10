"""多轮对话管理（P3）"""

from __future__ import annotations

from llm import LLMError, chat
from prompts import (
    OUT_OF_SCOPE_REPLY,
    SYSTEM_PROMPT,
    build_rag_user_message,
    build_retrieval_query,
    is_out_of_scope,
)
from retriever import retrieve_for_prompt


class Conversation:
    """维护 DeepSeek messages 历史，支持连续追问与边界处理。"""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        # (用户原始输入, 助手回复)，仅用于检索 query 改写
        self.raw_history: list[tuple[str, str]] = []

    def turn(self, user_input: str) -> str:
        user_input = user_input.strip()
        if not user_input:
            return "请输入与场馆/活动相关的问题。"

        if is_out_of_scope(user_input):
            answer = OUT_OF_SCOPE_REPLY
            self.messages.append({"role": "user", "content": user_input})
            self.messages.append({"role": "assistant", "content": answer})
            return answer

        retrieval_q = build_retrieval_query(user_input, self.raw_history)
        chunks = retrieve_for_prompt(retrieval_q)
        user_msg = build_rag_user_message(user_input, chunks)

        self.messages.append({"role": "user", "content": user_msg})
        try:
            answer = chat(self.messages)
        except LLMError:
            self.messages.pop()
            raise

        self.messages.append({"role": "assistant", "content": answer})
        self.raw_history.append((user_input, answer))
        return answer

    @property
    def turn_count(self) -> int:
        return len(self.raw_history)
