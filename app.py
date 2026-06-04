"""Gradio 网页入口（P5）：与 main.py 共用 Conversation / RAG / 边界逻辑。"""

from __future__ import annotations

import gradio as gr

from conversation import Conversation
from embedder import warmup
from llm import LLMError

warmup()
_conv = Conversation()

_INTRO = """
根据活动类型、人数、时间等推荐校园场馆，支持**多轮追问**；非场馆类问题（如转专业）将提示边界。

当前知识库为**示例假数据**（`knowledge/示例-*.md`）。补全本校场馆后执行 `python indexer.py --rebuild` 即可，无需改本页面代码。
"""

_EXAMPLES = [
    "我想要去羽毛球馆打羽毛球，想要环境好一点的",
    "我们一共15个人，需要预约吗",
    "东区有哪些场馆可以打球？",
    "怎么申请转专业",
]


def _chat(user_msg: str, history: list[dict] | None) -> tuple[list[dict], str, str]:
    history = list(history or [])
    if not (user_msg or "").strip():
        return history, "", _status_line()

    try:
        reply = _conv.turn(user_msg.strip())
    except LLMError as e:
        reply = f"[API 错误] {e}"

    history.append({"role": "user", "content": user_msg.strip()})
    history.append({"role": "assistant", "content": reply})
    return history, "", _status_line()


def _clear() -> tuple[list, str, str]:
    _conv.reset()
    return [], "", _status_line()


def _status_line() -> str:
    n = _conv.turn_count
    return f"已进行 **{n}** 轮有效对话（越界拒答不计入检索轮次）。"


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="校园智能场馆匹配平台") as demo:
        gr.Markdown("# 校园智能场馆匹配平台")
        gr.Markdown(_INTRO)
        chatbot = gr.Chatbot(label="对话", height=480)
        status = gr.Markdown(_status_line())
        with gr.Row():
            txt = gr.Textbox(
                label="你的问题",
                placeholder="例如：约 50 人室内羽毛球，要环境好一点的",
                scale=4,
                lines=2,
            )
            send = gr.Button("发送", variant="primary", scale=1)
        with gr.Row():
            clear_btn = gr.Button("清空会话")
        gr.Examples(examples=_EXAMPLES, inputs=txt, label="示例问题（点击填入）")

        inputs = [txt, chatbot]
        outputs = [chatbot, txt, status]
        txt.submit(_chat, inputs, outputs)
        send.click(_chat, inputs, outputs)
        clear_btn.click(_clear, None, outputs)

    return demo


if __name__ == "__main__":
    build_ui().launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,
        show_error=True,
    )
