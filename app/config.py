"""统一管理配置和环境变量。"""
import os
from dotenv import load_dotenv

# 本地从 .env 读取；云上环境变量由 Cloud Run 注入，找不到 .env 时什么都不做
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6").strip()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "").strip()

# 免费方案：只填 GROQ_API_KEY，语音识别和对话都走 Groq（有免费额度）
# 设置了 GROQ_API_KEY 就优先用 Groq；否则回落到 OpenAI Whisper + Claude
# 免费方案 2：Google Gemini（用 Google 账号在 https://aistudio.google.com/apikey 创建 Key）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip()
USE_GEMINI = bool(GEMINI_API_KEY)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo").strip()
USE_GROQ = bool(GROQ_API_KEY) and not USE_GEMINI   # 优先级：Gemini > Groq > OpenAI+Claude

# 限制，防止被刷或误传超大文件
MAX_AUDIO_BYTES = 10 * 1024 * 1024   # 录音最大 10MB
MAX_HISTORY_MESSAGES = 20            # 最多带最近 20 条历史（10 轮）

if USE_GEMINI:
    print("使用 Gemini（免费方案）：语音识别 + 对话")
elif USE_GROQ:
    print("使用 Groq（免费方案）：语音识别 + 对话")
else:
    if not ANTHROPIC_API_KEY:
        print("警告：未设置 GEMINI_API_KEY / GROQ_API_KEY / ANTHROPIC_API_KEY，AI 对话功能将无法使用")
    if not OPENAI_API_KEY:
        print("警告：未设置 GEMINI_API_KEY / GROQ_API_KEY / OPENAI_API_KEY，语音识别功能将无法使用")
