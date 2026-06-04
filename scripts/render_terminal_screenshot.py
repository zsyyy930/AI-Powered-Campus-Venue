"""将 CLI 测试实录渲染为终端风格 PNG（供实验报告/协作日志引用）。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "p3-main-cli-test-2026-06-04.png"

LINES = [
    "(.venv) PS ...校园智能场馆匹配平台> python main.py",
    "[embedder] 启动预热：预加载向量模型…",
    "[embedder] HuggingFace 镜像: https://hf-mirror.com",
    "[embedder] 加载语义模型 sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "            （仅本地缓存，不访问 huggingface.co）",
    "Loading weights: 100%|██████████| 199/199 [00:00<00:00, 3643.59it/s]",
    "[embedder] 模型就绪（本地目录）",
    "[embedder] 预热完成",
    "校园智能场馆匹配平台（P3 多轮 + 边界）",
    "命令：quit 退出 | reset 清空对话历史",
    "",
    "你：我想要去羽毛球馆打羽毛球，想要环境好一点的",
    "",
    "助手：根据参考资料，本校的羽毛球场地信息如下：",
    "  - 位置：东区体育中心（羽毛球分馆）",
    "  - 容量：约500人  - 适用活动：羽毛球",
    "  该场馆是室内场馆，环境相对较好…",
    "  （参考资料未记载的灯光/地板等，建议联系体育部核实。）",
    "",
    "（本轮结束，已进行 1 轮有记录的对话）",
    "----------------------------------------",
    "",
    "你：我们一共15个人，需要预约吗",
    "",
    "助手：…羽毛球分馆…预约方式：校园场馆系统，提前 3–7 个工作日…",
    "  15人的团队完全没问题。",
    "",
    "（本轮结束，已进行 2 轮有记录的对话）",
    "----------------------------------------",
    "",
    "你：我想转去羽毛球专业，怎么转专业呢",
    "",
    "助手：您的问题似乎不属于「校园场馆/活动场地」范围…",
    "  教务、转专业等问题请咨询教务处；如需场馆帮助请描述活动类型、人数与时间。",
    "",
    "（本轮结束，已进行 2 轮有记录的对话）",
    "----------------------------------------",
    "",
    "※ 知识库：示例-体育馆.md / 示例-游泳馆.md（假数据，非本校真实信息）",
]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\Consola.ttf"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def main() -> None:
    font = _font(16)
    line_h = 22
    pad = 24
    max_w = max(font.getlength(line) for line in LINES)
    img_w = int(max_w) + pad * 2
    img_h = pad * 2 + line_h * len(LINES) + 36

    img = Image.new("RGB", (img_w, img_h), "#1e1e1e")
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, img_w, 28), fill="#323232")
    draw.text((pad, 6), "python main.py — P3 联调（示例知识库 / 假数据）", fill="#cccccc", font=_font(14))

    y = 36 + pad
    colors = {
        "你：": "#4ec9b0",
        "助手：": "#dcdcaa",
        "[embedder]": "#9cdcfe",
        "※": "#f48771",
    }
    default = "#d4d4d4"
    for line in LINES:
        color = default
        for prefix, c in colors.items():
            if line.startswith(prefix):
                color = c
                break
        if "Loading weights" in line:
            color = "#569cd6"
        draw.text((pad, y), line, fill=color, font=font)
        y += line_h

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"已保存: {OUT}")


if __name__ == "__main__":
    main()
