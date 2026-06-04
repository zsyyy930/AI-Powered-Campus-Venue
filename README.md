# 校园智能场馆匹配平台

基于大模型与检索的校园场馆智能匹配系统：根据用户需求（活动类型、人数、时间、设备等）推荐合适的校园场馆。

## 项目结构

```
校园智能场馆匹配平台/
├── README.md
├── requirements.txt
├── config.example.py    # 配置示例（复制为 config.py 后填写密钥）
├── llm.py               # 大模型 API 封装
├── embedder.py          # 文本向量化（P2）
├── indexer.py           # 知识库切块与建索引（P1/P2）
├── retriever.py         # 语义检索
├── prompts.py           # 系统 Prompt、边界判断（P3）
├── conversation.py      # 多轮对话 history（P3）
├── main.py              # 命令行入口
├── knowledge/           # 场馆知识库原始 Markdown
├── data/                # chunks.json、embeddings.npz（索引产物）
└── docs/
    ├── 实现阶段规划.md   # 分阶段实现分析（参考）
    ├── 名词解释.md       # RAG / Embedding / Gradio 简述
    ├── P0入门实战.md     # 从零带跑（建议先看）
    ├── P1P2入门实战.md   # 切块 + 向量检索
    ├── 小组分工建议.md   # 3 人分工与答辩准备
    ├── 实验报告.md
    └── AI协作日志.md
```

## 快速开始

| 阶段 | 教程 |
|------|------|
| P0 跑通 API + CLI | [`docs/P0入门实战.md`](docs/P0入门实战.md) |
| P1/P2 切块 + 向量检索 | [`docs/P1P2入门实战.md`](docs/P1P2入门实战.md) |
| P3 多轮 + 边界 | `python test_conversation.py` → `python main.py`（支持 `reset`） |

简要步骤（P0 完成后继续）：

1. 安装依赖：`pip install -r requirements.txt`
2. 配置：`Copy-Item config.example.py config.py`（DeepSeek Key + 向量相关项见 example）
3. 构建索引：`python indexer.py --rebuild`（改 knowledge 后都要重做）
4. 测试检索：`python test_retriever.py`
5. 测试 API：`python test_llm.py`
6. 运行：`python main.py`

## 注意事项

- **虚拟环境**：新开终端需再执行 `.\.venv\Scripts\Activate.ps1`，看到 `(.venv)` 再运行命令。
- **解释器**：在 Cursor 中运行脚本时，请选项目 `.venv` 里的 Python。
- **响应较慢**：`main.py` 需联网调用 DeepSeek，调试时把问题写短一些。
- **检索不准**：可调 `config.py` 中 `SIMILARITY_THRESHOLD`（如 0.25～0.45）；修改 `knowledge/` 后必须 `python indexer.py --rebuild`。
- **知识库数量**：任务书要求 `knowledge/` 下 **≥15 个**场馆 `.md` 文件（每个馆一份，如 `东区体育馆.md`）。文件内的 `##` 小节只影响 RAG 切块条数，不等于 15 份资料。
- **索引文件**：`data/chunks.json` 可提交；`data/embeddings.npz` 体积大已 gitignore，队友 clone 后需本地 `--rebuild`。
- **模型下载**：Embedding 需从 HuggingFace 拉模型；连不上时可设 `$env:HF_ENDPOINT = "https://hf-mirror.com"` 再执行 `indexer.py --rebuild`（见 P1P2 教程）。

## 环境要求

- Python 3.10+

## 给队友 / 新克隆项目的人

代码可以 Git 共享，**API Key 不能**。仓库里的 `.gitignore` 已忽略 `config.py`，每人需在本机单独配置：

1. 克隆或复制项目后，进入项目根目录。
2. 安装依赖（建议使用虚拟环境，见 [`docs/P0入门实战.md`](docs/P0入门实战.md) 第 2–3 步）。
3. 创建本地配置（Windows PowerShell）：
   ```powershell
   Copy-Item config.example.py config.py
   ```
4. 打开 `config.py`，将 `API_KEY` 改为你自己在 [DeepSeek 开放平台](https://platform.deepseek.com) 申请的 Key。
5. 依次自检：`python test_retriever.py` → `python test_llm.py` → `python main.py`。

**请勿**把 `config.py` 提交到 Git、发群聊或打进作业 zip。可提交的只有 `config.example.py`（模板，无真实密钥）。

若教师统一发放课程 Key，由组长私下发给组员填入各自 `config.py`，同样不要写入仓库。

## 提交作业前检查

- [ ] 压缩包 / 仓库中**没有** `config.py`、`.env`
- [ ] 含有 `README.md`、`requirements.txt`、`config.example.py`、完整源代码与 `knowledge/`
- [ ] 他人按本 README 复制 `config.example.py` 并填入自己的 Key 后可运行
