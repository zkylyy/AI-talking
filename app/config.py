"""
统一管理配置和环境变量。
其他模块都从这里 import，不要在各处分散写 os.getenv()，方便以后维护。
"""
import os
from dotenv import load_dotenv

# 本地开发时从 .env 文件加载；部署到 Cloud Run 时环境变量由 --set-env-vars 传入，
# 这行代码不会报错，只是找不到 .env 文件时什么都不做。
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# Cloud Run 会通过 PORT 环境变量告诉容器要监听哪个端口，本地开发默认用 8080
PORT = int(os.getenv("PORT", "8080"))

if not ANTHROPIC_API_KEY:
    print("警告：未设置 ANTHROPIC_API_KEY，LLM 对话功能将无法使用")
if not OPENAI_API_KEY:
    print("警告：未设置 OPENAI_API_KEY，语音识别功能将无法使用")
