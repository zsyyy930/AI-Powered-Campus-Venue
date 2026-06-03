"""大模型 API 封装（DeepSeek，OpenAI 兼容接口）"""

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

try:
    import config
except ImportError as e:
    raise ImportError(
        "未找到 config.py。请复制 config.example.py 为 config.py 并填写 API_KEY。"
    ) from e


class LLMError(Exception):
    """调用大模型失败时抛出，便于上层显示友好提示"""


def get_client() -> OpenAI:
    if not getattr(config, "API_KEY", None) or config.API_KEY.startswith("在这里"):
        raise LLMError("请先在 config.py 中填写有效的 API_KEY。")
    timeout = getattr(config, "API_TIMEOUT", 60)
    return OpenAI(
        api_key=config.API_KEY,
        base_url=config.API_BASE,
        timeout=timeout,
    )


def chat(
    messages: list[dict],
    temperature: float | None = None,
) -> str:
    """
    调用 DeepSeek 对话接口。

    messages 示例：
        [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "你好"},
        ]
    """
    temp = temperature if temperature is not None else getattr(config, "TEMPERATURE", 0.3)
    model = config.MODEL_NAME
    max_retries = getattr(config, "API_MAX_RETRIES", 2)
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            client = get_client()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temp,
            )
            content = response.choices[0].message.content
            return content or ""
        except RateLimitError as e:
            last_error = e
            hint = "请求过于频繁，请稍后再试。"
        except APIConnectionError as e:
            last_error = e
            hint = "网络连接失败，请检查网络或 API 地址。"
        except APIStatusError as e:
            last_error = e
            hint = f"API 返回错误（{e.status_code}）：{e.message}"
        except Exception as e:
            last_error = e
            hint = str(e)

        if attempt < max_retries:
            continue

    raise LLMError(hint) from last_error
