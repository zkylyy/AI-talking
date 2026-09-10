"""
LLM 对话服务。
用 Claude API 扮演一个英语口语教练的角色：
- 用简单口语化的英语回复，像真人聊天一样自然
- 根据用户设置的水平调整用词难度
- 顺手纠正用户明显的语法/用词错误，但不会打断对话节奏
"""
from anthropic import Anthropic
from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# system prompt 是整个"教练人设"的核心，以后想调整 AI 的说话风格、纠错方式，
# 主要就是改这里的文字，不需要动其他代码。
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


async def get_reply(user_text: str, history: list[dict], level: str = "intermediate") -> str:
    """
    生成 AI 教练的回复。

    参数：
        user_text: 用户刚说的话（已经过 STT 转成文字）
        history: 之前的对话记录，格式为 [{"role": "user"/"assistant", "content": "..."}]
        level: 用户英语水平，beginner / intermediate / advanced

    返回：
        AI 的回复文本（后面会传给 TTS 转成语音）
    """
    messages = history + [{"role": "user", "content": user_text}]

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT.format(level=level),
        messages=messages,
    )

    # response.content 是一个 block 列表，正常文本回复只有一个 text block，
    # 这里简单取第一个 block 的文本内容即可。
    return response.content[0].text.strip()
