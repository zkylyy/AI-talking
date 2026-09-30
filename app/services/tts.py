"""TTS：edge-tts（免费但非官方接口，偶尔会失效，所以调用方要做好失败兜底）。"""
import io
import edge_tts

VOICE = "en-US-AriaNeural"


async def synthesize_speech(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, VOICE)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()
