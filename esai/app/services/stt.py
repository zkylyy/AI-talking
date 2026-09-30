"""STT：优先 Gemini（免费），其次 Groq Whisper（免费），最后 OpenAI Whisper（付费）。"""
from openai import AsyncOpenAI
from app.config import OPENAI_API_KEY, GROQ_API_KEY, GROQ_BASE_URL, GROQ_STT_MODEL, USE_GROQ, USE_GEMINI
from app.services import gemini

_client = None


def _get_client() -> AsyncOpenAI:
    # 延迟初始化：key 没配对时容器也能正常启动，调用时才报错
    global _client
    if _client is None:
        if USE_GROQ:
            # Groq 兼容 OpenAI 接口，只需换 base_url
            _client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
        else:
            _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    if USE_GEMINI:
        return await gemini.transcribe(audio_bytes, filename)
    transcript = await _get_client().audio.transcriptions.create(
        model=GROQ_STT_MODEL if USE_GROQ else "whisper-1",
        file=(filename, audio_bytes),
        language="en",
    )
    return transcript.text.strip()
