"""
主程序入口。
把 STT → LLM → TTS 三个环节串起来，对外提供一个 /api/chat 接口：
前端传一段录音上来，返回识别出的文字 + AI 回复文字 + AI 回复的语音。
"""
import base64
import re
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.services.stt import transcribe_audio
from app.services.llm import get_reply
from app.services.tts import synthesize_speech

app = FastAPI(title="English Speaking AI")

# 允许跨域调用。如果你的前端和后端部署在不同域名下（比如前端用 Cloudflare Pages，
# 后端用 Cloud Run），需要打开这个；如果就一个服务自己托管前端，其实可以不开。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议换成你自己的具体域名，而不是 "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ 重要提醒（见 README）：
# 这是一个非常简单的内存存储，仅适合本地开发和单实例小规模测试。
# Cloud Run 在有并发流量时会自动开多个容器实例，各实例内存不共享，
# 用户的请求可能被分发到不同实例，导致"AI 突然忘记之前聊过什么"。
# 生产环境请换成 Redis / Firestore 等外部存储来保存 session。
SESSIONS: dict[str, list[dict]] = {}

MAX_HISTORY_TURNS = 10  # 只保留最近10轮对话，避免上下文无限增长、消耗过多 token


@app.get("/health")
async def health_check():
    """健康检查接口，Cloud Run 用它判断容器是否正常启动。"""
    return {"status": "ok"}


@app.post("/api/session")
async def create_session():
    """开始一段新对话，返回一个 session_id，后续 /api/chat 请求都带上这个 id。"""
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = []
    return {"session_id": session_id}


@app.post("/api/chat")
async def chat(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    level: str = Form("intermediate"),  # beginner / intermediate / advanced
):
    """
    核心对话接口。

    流程：接收录音 → Whisper 转文字 → Claude 生成回复 → edge-tts 合成语音 → 一起返回。
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="session_id 不存在，请先调用 /api/session")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="音频文件是空的")

    # 1. 语音识别：用户说的话 → 英文文字
    user_text = await transcribe_audio(audio_bytes, filename=audio.filename or "audio.webm")
    if not user_text:
        raise HTTPException(status_code=400, detail="没有识别到有效的语音内容，请再说一次")

    # 2. 取出这个 session 的历史记录，生成 AI 回复
    history = SESSIONS[session_id]
    ai_text = await get_reply(user_text, history, level=level)

    # 3. 更新历史记录，并裁剪长度避免无限增长
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": ai_text})
    SESSIONS[session_id] = history[-MAX_HISTORY_TURNS * 2:]

    # 4. 语音合成：把纠错提示（💡 Tip 部分）去掉再读，只朗读正常对话内容，
    #    Tip 文字仍然会完整返回给前端用文字展示。
    speech_text = re.sub(r"💡 Tip:.*", "", ai_text, flags=re.DOTALL).strip()
    audio_reply = await synthesize_speech(speech_text)

    return {
        "user_text": user_text,
        "ai_text": ai_text,
        # 音频用 base64 编码直接塞进 JSON 返回，对于几秒钟的短语音这样做最简单；
        # 如果以后语音变长，可以考虑改成返回一个临时下载链接（比如存到 Cloud Storage）。
        "audio_base64": base64.b64encode(audio_reply).decode("utf-8"),
    }


# 把 static/ 目录下的前端页面挂载到根路径，这样浏览器直接访问域名就能看到页面，
# 不需要单独再部署一个前端服务。必须放在所有 /api 路由之后，避免路径冲突。
app.mount("/", StaticFiles(directory="static", html=True), name="static")
