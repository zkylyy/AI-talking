"""LLM：优先 Gemini（免费），其次 Groq（免费），最后 Claude（付费）。"""
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL, USE_GROQ, USE_GEMINI,
)
from app.services import gemini

_anthropic = None
_groq = None

SYSTEM_PROMPT = """You are a friendly, patient English speaking coach having a natural voice conversation with a learner.

Rules:
1. Keep replies short and conversational (2-4 sentences), like real spoken English — this will be converted to speech.
2. Match the learner's level: {level}. Use simpler vocabulary and shorter sentences for beginners.
3. If the learner made a clear grammar or word-choice mistake, gently mention ONE correction at the end,
   in this exact format on a new line: "💡 Tip: ..." — keep it brief, don't lecture.
4. If there's no mistake worth mentioning, skip the tip entirely.
5. Ask a natural follow-up question to keep the conversation going, like a real friend would.
6. Never break character to explain that you are an AI language model.
"""


async def _reply_groq(messages: list[dict], system: str) -> str:
    global _groq
    if _groq is None:
        _groq = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
    kwargs = {}
    if GROQ_MODEL.startswith("openai/gpt-oss"):
        # 推理模型：降低思考量，回复更快，也不会把 token 都花在思考上
        kwargs["reasoning_effort"] = "low"
    resp = await _groq.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1000,
        messages=[{"role": "system", "content": system}] + messages,
        **kwargs,
    )
    return (resp.choices[0].message.content or "").strip()


async def _reply_claude(messages: list[dict], system: str) -> str:
    global _anthropic
    if _anthropic is None:
        _anthropic = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    resp = await _anthropic.messages.create(
        model=CLAUDE_MODEL, max_tokens=300, system=system, messages=messages,
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


async def get_reply(user_text: str, history: list[dict], level: str = "intermediate") -> str:
    messages = history + [{"role": "user", "content": user_text}]
    system = SYSTEM_PROMPT.format(level=level)
    if USE_GEMINI:
        return await gemini.reply(messages, system)
    if USE_GROQ:
        return await _reply_groq(messages, system)
    return await _reply_claude(messages, system)
