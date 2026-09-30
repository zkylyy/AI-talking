"""
主程序：STT → LLM → TTS。
无状态设计：对话历史由前端保存，每次请求带上来，
这样 Cloud Run 缩容/多实例都不会丢上下文。
"""
import base64
import json
import logging
import re
import secrets

from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.staticfiles import StaticFiles

from app.config import ACCESS_TOKEN, MAX_AUDIO_BYTES, MAX_HISTORY_MESSAGES
from app.services.stt import transcribe_audio
from app.services.llm import get_reply
from app.services.tts import synthesize_speech

logger = logging.getLogger("english-speaking-ai")
app = FastAPI(title="English Speaking AI")

VALID_LEVELS = {"beginner", "intermediate", "advanced"}


def check_token(token: str | None):
    """如果设置了 ACCESS_TOKEN，就要求请求头带上正确口令。"""
    if not ACCESS_TOKEN:
        return
    if not token or not secrets.compare_digest(token, ACCESS_TOKEN):
        raise HTTPException(status_code=401, detail="访问口令不正确")


def parse_history(raw: str) -> list[dict]:
    """解析并清洗前端传来的历史记录，只保留合法的最近若干条。"""
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="history 格式不正确")
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="history 格式不正确")

    clean = []
    for m in data:
        if (
            isinstance(m, dict)
            and m.get("role") in ("user", "assistant")
            and isinstance(m.get("content"), str)
            and m["content"].strip()
        ):
            clean.append({"role": m["role"], "content": m["content"][:2000]})
    clean = clean[-MAX_HISTORY_MESSAGES:]
    # Claude 要求第一条必须是 user
    while clean and clean[0]["role"] != "user":
        clean.pop(0)
    return clean


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/auth-required")
async def auth_required():
    """前端用它判断要不要弹出口令输入框。"""
    return {"required": bool(ACCESS_TOKEN)}


@app.post("/api/chat")
async def chat(
    audio: UploadFile = File(...),
    history: str = Form("[]"),
    level: str = Form("intermediate"),
    x_access_token: str | None = Header(default=None),
):
    check_token(x_access_token)

    if level not in VALID_LEVELS:
        level = "intermediate"

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="音频文件是空的")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="录音太长了，请说短一点（不超过约 1 分钟）")

    past = parse_history(history)

    # 1. 语音识别
    try:
        user_text = await transcribe_audio(audio_bytes, filename=audio.filename or "audio.webm")
    except Exception as e:
        logger.exception("STT failed")
        raise HTTPException(status_code=502, detail=f"语音识别失败（检查 API Key 是否填对、额度是否用完）：{type(e).__name__}")
    if not user_text:
        raise HTTPException(status_code=400, detail="没有识别到语音内容，请再说一次")

    # 2. AI 回复
    try:
        ai_text = await get_reply(user_text, past, level=level)
    except Exception as e:
        logger.exception("LLM failed")
        raise HTTPException(status_code=502, detail=f"AI 回复失败（检查 API Key、模型名 GROQ_MODEL 是否有效，或稍后再试）：{type(e).__name__}")

    # 3. 语音合成：不朗读 Tip 部分。TTS 失败不影响文字结果。
    speech_text = re.sub(r"💡 Tip:.*", "", ai_text, flags=re.DOTALL).strip()
    audio_b64 = None
    if speech_text:
        try:
            audio_reply = await synthesize_speech(speech_text)
            if audio_reply:
                audio_b64 = base64.b64encode(audio_reply).decode("utf-8")
        except Exception:
            logger.exception("TTS failed (returning text only)")

    return {"user_text": user_text, "ai_text": ai_text, "audio_base64": audio_b64}


# 前端页面，必须放在所有 /api 路由之后
app.mount("/", StaticFiles(directory="static", html=True), name="static")
