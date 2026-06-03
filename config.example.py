# 使用说明：复制本文件为 config.py，填入你的 DeepSeek API Key
# 命令（在项目根目录 PowerShell）：
#   Copy-Item config.example.py config.py

# ========== DeepSeek 大模型（任务书要求）==========
API_BASE = "https://api.deepseek.com"
API_KEY = "在这里粘贴你的-key"
MODEL_NAME = "deepseek-chat"

# 生成风格：问答建议偏低，减少胡编（0.0~2.0）
TEMPERATURE = 0.3

# 网络超时（秒）
API_TIMEOUT = 60
API_MAX_RETRIES = 2

# ========== 知识库与检索（P0 仍用关键词，P2 再改向量）==========
KNOWLEDGE_DIR = "knowledge"
TOP_K = 5

# 拼进 Prompt 的最多场馆条数（控制费用与长度）
MAX_VENUES_IN_PROMPT = 3
