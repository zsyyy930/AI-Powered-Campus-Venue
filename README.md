# 校园智能场馆匹配平台

基于大模型与检索的校园场馆智能匹配系统：根据用户需求（活动类型、人数、时间、设备等）推荐合适的校园场馆。

## 项目结构

```
校园智能场馆匹配平台/
├── README.md
├── requirements.txt
├── config.example.py    # 配置示例（复制为 config.py 后填写密钥）
├── llm.py               # 大模型 API 封装
├── retriever.py         # 场馆知识检索与匹配
├── main.py              # 程序入口
├── knowledge/           # 场馆知识库数据
└── docs/
    ├── 实现阶段规划.md   # 分阶段实现分析（参考）
    ├── 名词解释.md       # RAG / Embedding / Gradio 简述
    ├── P0入门实战.md     # 从零带跑（建议先看）
    ├── 小组分工建议.md   # 3 人分工与答辩准备
    ├── 实验报告.md
    └── AI协作日志.md
```

## 快速开始

**第一次上手请跟详细教程**：[`docs/P0入门实战.md`](docs/P0入门实战.md)（逐步带跑，含排错表）

简要步骤：

1. 创建虚拟环境并安装依赖：`pip install -r requirements.txt`
2. 复制配置：`Copy-Item config.example.py config.py`，填入 DeepSeek API Key
3. 测试 API：`python test_llm.py`
4. 测试检索：`python test_retriever.py`
5. 运行完整程序：`python main.py`

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
