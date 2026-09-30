"""Gemini（Google AI Studio 免费额度）：用 REST 直接调用，语音识别 + 对话都走它。"""
import base64
import httpx
from app.config import GEMINI_API_KEY, GEMINI_MODEL

BASE = "https://generativelanguage.googleapis.com/v1beta/models"

MIME_BY_EXT = {
    "wav": "audio/wav", "mp3": "audio/mp3", "ogg": "audio/ogg",
    "webm": "audio/webm", "mp4": "audio/mp4", "m4a": "audio/mp4",
}

TRANSCRIBE_PROMPT = (
    "Transcribe this English speech exactly as spoken, word for word. "
    "Do NOT correct grammar, do NOT fix mistakes, do NOT add punctuation-based rewording. "
    "Output ONLY the transcript text, nothing else. "
    "If there is no intelligible speech, output an empty string."
)


async def _generate(body: dict) -> str:
    url = f"{BASE}/{GEMINI_MODEL}:generateContent"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=body, headers={"x-goog-api-key": GEMINI_API_KEY})
    if r.status_code != 200:
        # 抛出带状态码和 Google 返回信息的错误，方便在日志里排查
        raise RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()


async def transcribe(audio_bytes: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
    mime = MIME_BY_EXT.get(ext, "audio/wav")
    body = {
        "contents": [{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(audio_bytes).decode()}},
                {"text": TRANSCRIBE_PROMPT},
            ],
        }],
        "generationConfig": {"maxOutputTokens": 1000},
    }
    return await _generate(body)


async def reply(messages: list[dict], system: str) -> str:
    contents = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
        for m in messages
    ]
    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 1000},
    }
    return await _generate(body)
