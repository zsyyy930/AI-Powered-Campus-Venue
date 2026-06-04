# AI 协作日志

记录与 AI 协作完成「校园智能场馆匹配平台」的关键步骤，便于实验报告引用与**后续会话接续开发**。

---

## 协作记录

| 日期 | 协作内容 | 采纳情况 | 备注 |
|------|----------|----------|------|
| 2026-06-03 | 在 Cursor 安装 **Office Viewer**（`cweijan.vscode-office`），用于预览任务书 `.docx` | 已采纳 | 用户设置中保留 `*.md` 使用默认编辑器，避免影响 Markdown 工作流 |
| 2026-06-03 | 按任务书「方向一-知识问答助手」脚手架，在 `大作业/` 下新建 **校园智能场馆匹配平台** 并搭好目录与占位代码 | 已采纳 | 工作区当时无方向一实体代码，按截图结构搭建；业务语义改为场馆匹配 |
| 2026-06-03 | 建立本协作日志，约定后续关键交互均写入此文件 | 已采纳 | 见下文「项目接续指南」 |
| 2026-06-03 | 对照任务书梳理实现路线图：必做（RAG/多轮/边界/CLI）+ 进阶（向量检索/Gradio） | 已采纳 | 详见下文「实现路线图（2026-06-03 定稿）」 |
| 2026-06-03 | 将分阶段分析整理为参考文档 `docs/实现阶段规划.md` | 已采纳 | 含 P0–P6 目标、技术要点、风险、完成标准、时间线 |
| 2026-06-03 | 启动并完成 **P0**：DeepSeek 联调、自检脚本、`.gitignore`、推送 GitHub | 已完成 | 见下文「P0 完成摘要」；远程仓库 `Yu-lorde/AI-Powered-Campus-Venue` |
| 2026-06-03 | README 补充队友配置说明；厘清 `config.py` 仅本地、不入库 | 已采纳 | 队友 clone 后复制 `config.example.py` 自填 Key |
| 2026-06-03 | P0 常见问题迁至 README「注意事项」 | 已采纳 | `P0入门实战.md` 改为指向 README |
| 2026-06-03 | 实现 **P1/P2 代码** + `docs/P1P2入门实战.md`；用户暂离，进度见「暂停接续备忘」 | 已完成 | 语义向量已在 VPN 下跑通 |
| 2026-06-04 | **P3**：`prompts.py` + `conversation.py` 多轮与边界；`test_conversation.py`、`docs/测试用例.md` | 已采纳 | 可先用示例 knowledge 测，不依赖 15 个 md |
| 2026-06-04 | 今日收工：P3 代码已写，`test_conversation.py` 离线通过；`main.py` 多轮联调**未测完** | 待续 | 见「暂停接续备忘」 |
| 2026-06-04 | **P3 联调完成**：`main.py` 三轮对话（推荐 / 多轮预约 / 转专业越界）；实录写入 `docs/实验报告.md` §4 | 已采纳 | 终端截图 `docs/images/p3-main-cli-test-2026-06-04.png`（示例假数据） |
| 2026-06-04 | 本地语义模型：`EMBEDDING_LOCAL_ONLY`、repo_id 修正、`warmup()`；`docs/名词解释.md` 扩充 | 已采纳 | 校园网可不连 huggingface.co |

> **维护约定**：每完成一轮有意义的协作（定方案、改模块、联调、写报告段落等），在表中追加一行，并同步更新「当前进度」与「待办」。

---

## 项目接续指南（给下一轮 AI / 给自己）

### 1. 项目定位

- **课程**：人工智能基础 A 大作业  
- **选题**：校园智能场馆匹配平台（对标方向一：检索 + 大模型问答/推荐）  
- **根目录**：`d:\大学启动\人工智能基础A\大作业\校园智能场馆匹配平台\`  
- **任务书**：`../人工智能基础-大作业任务书.docx`（需 Office Viewer 或 Word 打开）

### 2. 当前架构（已实现）

```
knowledge/*.md
    → indexer.py --rebuild → data/chunks.json [+ embeddings.npz]
用户问题 → retriever.py（向量或关键词）→ main.py → llm.py(DeepSeek)
```

| 文件 | 职责 | 实现状态 |
|------|------|----------|
| `indexer.py` / `embedder.py` | P1 切块、P2 向量化 | 代码已提交 |
| `retriever.py` | 语义检索；无向量时回退关键词 | 已实现 |
| `data/chunks.json` | RAG 切块索引 | 6 段（2 个示例 md 切块而来） |
| `knowledge/*.md` | 场馆文档 | **2 个文件**（任务书要求 **≥15 个** .md，非 15 个切块） |
| `data/embeddings.npz` | 向量索引 | **本机待生成**（HuggingFace 曾超时） |
| `config.py` | 含向量相关项 | **用户需对照 example 补全** |
| `llm.py` / `main.py` / `test_*` | P0 流程 | 用户曾跑通 `test_llm.py` |
| `knowledge/` | 示例体育馆、游泳馆 共 2 个 md | 待补至 **≥15 个**本校场馆文件 |

### 3. 当前进度

- [x] P0：DeepSeek + CLI + GitHub  
- [x] P1 代码；`data/chunks.json` 已生成（6 段）  
- [ ] P2 向量：`embeddings.npz` 待本机 `--rebuild`（建议 HF 镜像）  
- [ ] `config.py` 补全 P1/P2 配置项（见暂停备忘）  
- [ ] `knowledge/` **≥15 个**场馆 `.md` 文件  
- [x] **P3** 多轮 + 边界（代码完成）  
- [x] **P3 联调**：`python main.py` 三轮实测（示例知识库）；截图见下文  
- [ ] `knowledge/` **≥15 个** `.md` 本校文件  
- [ ] P5 Gradio；实验报告  

### 4. 建议的下一步（优先级）

见下文 **「暂停接续备忘（回来先做）」**。

### 4b. 暂停接续备忘（回来先做）

**当前状态（2026-06-04）**：P0–P3 联调已跑通（`main.py` 三轮 + 边界）；知识库仍为 **2 个示例 md（假数据）**；实验报告 §4 已写文字实录 + 截图。

1. 激活环境：`cd` 项目根目录 → `.\.venv\Scripts\Activate.ps1`  
2. 在 `knowledge/` 补满 **≥15 个**本校场馆 `.md` → `python indexer.py --rebuild`  
3. 可选：按 `docs/测试用例.md` 补测 T4–T6（`reset`、追问「第二个」等）  
4. 后续：P5 Gradio、完善实验报告 §一–三/五  
5. Git：`git add .` → `commit` → `push`（勿含 `config.py`）

### 5. 与新 AI 协作时的推荐开场

复制下面一段话发给 AI，可快速恢复上下文：

```text
我在做「校园智能场馆匹配平台」（人工智能基础 A 大作业）。
项目路径：d:\大学启动\人工智能基础A\大作业\校园智能场馆匹配平台
请先阅读 docs/AI协作日志.md 和 README.md，在现有 retriever + llm + main 骨架上继续开发。
当前待办：P3 代码已有，下次先 `python main.py` 联调测试；见日志「暂停接续备忘」
```

### 6. 技术决策备忘（避免重复讨论）

| 决策点 | 当前选择 | 可变更条件 |
|--------|----------|------------|
| 脚手架来源 | 对齐「方向一-知识问答助手」目录结构 | 若任务书明确要求其他结构再调整 |
| 检索方式 | 简单关键词计分 | 知识库变大或同义词多时改向量检索 |
| LLM 接入 | OpenAI 兼容 SDK（`openai` 包） | 若用国内 API，改 `API_BASE` 即可 |
| 配置管理 | `config.example.py` + 本地 `config.py`（勿提交密钥） | 可改用 `.env` + `python-dotenv` |

### 7. 环境与工具

- **Python**：用户环境中有 3.13（见 Cursor `settings.json` 中 python 路径）  
- **编辑器**：Cursor；已装 `cweijan.vscode-office` 预览 docx  
- **运行入口**：项目根目录执行 `python main.py`

### 8. 协作日志更新模板（复制使用）

```markdown
| YYYY-MM-DD | [做了什么] | 已采纳 / 部分采纳 / 未采纳 | [原因或文件变更] |
```

---

## 详细步骤记录（按时间展开）

### 2026-06-03 — 环境与文档

- **问题**：任务书 `.docx` 在编辑器中无法正常阅读。  
- **处理**：安装扩展 `cweijan.vscode-office`；在 `%APPDATA%\Cursor\User\settings.json` 中为 `*.md` / `*.markdown` 指定 `default` 编辑器，避免 Office Viewer 接管 Markdown。  
- **接续提示**：修改任务书要求时，用 Office Viewer 或 Word 打开 `人工智能基础-大作业任务书.docx`。

### 2026-06-03 — 初始化项目脚手架

- **需求**：在 `大作业` 文件夹内新建「校园智能场馆匹配平台」，结构同方向一。  
- **产出文件**：  
  - 根目录：`README.md`、`requirements.txt`、`config.example.py`、`llm.py`、`retriever.py`、`main.py`  
  - `knowledge/示例-体育馆.md`（示例数据，上线前应换成本校场馆）  
  - `docs/实验报告.md`（空模板）、`docs/AI协作日志.md`（本文件）  
- **未做事项**：未创建 `config.py`（含密钥）；未运行联调；未读取任务书全文（docx 二进制未在本环境解析）。  
- **接续提示**：下一轮协作应**优先对照任务书**核对评分点，再决定是否要 Gradio/Web、向量库、日志格式等。

### 2026-06-03 — 建立协作日志机制

- **约定**：用户与 AI 的关键交互步骤写入本文件；每轮结束更新「协作记录表」「当前进度」「待办」。  
- **目的**：实验报告可引用 AI 协作过程；换会话或换模型时可无缝接续。

### 2026-06-03 — P0 完成摘要

- **配置**：`config.example.py` 改为 DeepSeek；用户本地 `config.py` 已填 Key（未入库）。  
- **代码**：`llm.py` 增加 `LLMError`、重试；`main.py` 捕获 API 错误；`retriever.py` 无 config 时可默认检索自检。  
- **知识库**：`knowledge/示例-体育馆.md`、`示例-游泳馆.md`（2 文件，待换本校真数据）。  
- **文档**：`docs/P0入门实战.md`；README 队友配置与提交检查。  
- **验证**：`python test_llm.py` 调用成功；检索自检可加载 2 文件。  
- **协作**：虚拟环境 `.venv`；Git 首次提交并 push 至 `https://github.com/Yu-lorde/AI-Powered-Campus-Venue`（18 文件，无 `config.py`）。  
- **未做（属 P1+）**：多轮对话、边界 Prompt、向量检索、Gradio、知识库 ≥15 段。

### 2026-06-04 — P3 `main.py` 联调（示例知识库）

- **环境**：`.venv`，`sentence_transformers` + 本地缓存 + 启动预热；DeepSeek API 正常。  
- **知识库**：仅 `示例-体育馆.md`、`示例-游泳馆.md`（**假数据**，非本校真实场馆）。  
- **实测三轮**（同一会话）：  
  1. 羽毛球馆推荐 → 命中东区体育中心，引用容量/室内信息  
  2. 15 人是否需预约 → 多轮承接，引用「提前 3–7 个工作日」  
  3. 转专业 → 越界拒答，未编造场馆  
- **产出**：`docs/实验报告.md` §4 文字实录；终端风格截图如下（由 `scripts/render_terminal_screenshot.py` 根据实录生成，标注假数据）：

![P3 main.py 联调截图（示例知识库 / 假数据）](images/p3-main-cli-test-2026-06-04.png)

- **待办**：替换 ≥15 个本校 md 后复测并更新报告截图。

### 2026-06-03 — P1/P2 代码落地（用户暂离）

- **新增**：`indexer.py`、`embedder.py`；改造 `retriever.py`、`main.py`、`test_retriever.py`；`docs/P1P2入门实战.md`；README 注意事项 + P1P2 快速开始。  
- **知识库**：示例 md 改为按 `##` 切块；`indexer --rebuild` 产出 **6 段** → `data/chunks.json`。  
- **阻塞**：本机连 `huggingface.co` 超时，**`embeddings.npz` 未生成**；教程已写镜像 `HF_ENDPOINT=https://hf-mirror.com`。  
- **回退**：无向量时 `retriever` 对 `chunks.json` 做关键词检索，仍可跑 `test_retriever.py`。  
- **用户状态**：P0 `test_llm.py` 已成功；稍后回来按「暂停接续备忘」继续。

---

## 变更文件索引（便于 diff / 报告附录）

| 路径 | 说明 |
|------|------|
| `校园智能场馆匹配平台/*` | 2026-06-03 一次性初始化的全部脚手架 |
| `docs/images/p3-main-cli-test-2026-06-04.png` | P3 CLI 联调截图（示例假数据） |
| `docs/实验报告.md` §4 | 三轮对话实录 + 图 1 |
| `scripts/render_terminal_screenshot.py` | 可重新生成报告用终端截图 |
| `Cursor/User/settings.json` | 仅用户本机；为 docx/Markdown 编辑器关联，**不属于项目仓库** |

---

## 实现路线图（2026-06-03 定稿）

**目标对齐**：选题落在任务书「图书馆与场馆助手」范畴；项目名「校园智能场馆匹配平台」= 场馆场景的 RAG 问答/推荐。

**用户优先级**（本轮确认）：
1. 必做：方向一基础功能，重点 **边界处理** + **多轮上下文**
2. 必做升级：**文本向量化语义检索**（替代当前关键词 `retriever.py`）
3. 后期优化：特定场景回复灵活性（Prompt 细化）
4. 交付增强：**Gradio 网页聊天**（任务书进阶加分项）

**API 约束**：智能对话必须使用 **DeepSeek API**（`base_url=https://api.deepseek.com`，`model=deepseek-chat`），Key 放 `config.py` 勿提交。

**知识库硬性指标**：`knowledge/` 下 **≥15 个**本校场馆 `.md` 文件（每馆一份）；文件内 `##` 仅用于 RAG 切块。

**推荐实施阶段**（共 6 期，前 4 期为必做闭环）：

| 阶段 | 内容 | 主要改动文件 |
|------|------|----------------|
| P0 | 跑通 DeepSeek + knowledge ≥15 个 md | `config.py`, `knowledge/`, `llm.py` |
| P1 | 文档切块 + 索引构建脚本 | 新增 `indexer.py`, `data/chunks.json` 或 `vectors.npz` |
| P2 | 向量语义检索替换关键词 | `retriever.py`, `embedder.py` |
| P3 | 多轮对话 + 边界处理 Prompt | 新增 `conversation.py`, `prompts.py`, 改 `main.py` |
| P4 | CLI 联调与测试用例 | `main.py`, `tests/` 或 `docs/测试用例.md` |
| P5 | Gradio 网页 | 新增 `app.py` |
| P6 | 加分项：引用标注、有无知识库对比实验 | `main.py` / 报告 |

**P0 已完成**；**P1 部分完成**（6 段索引）；**P2 待本机 rebuild 向量**。

---

*最后更新：2026-06-04（P3 main 联调完成，报告 §4 + 截图已入库）*
