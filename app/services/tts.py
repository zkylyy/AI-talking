"""
TTS（Text-to-Speech，文字转语音）服务。
用的是 edge-tts —— 一个调用微软 Edge 浏览器朗读接口的开源库，免费、不需要 API Key，
音质也还不错。缺点是它调用的是非官方接口，稳定性不如付费的 OpenAI TTS / Azure TTS，
以后要做商用产品建议换掉（接口形状类似，替换成本不高）。
"""
import io
import edge_tts

# en-US-AriaNeural 是一个自然的美式英语女声，edge-tts 还提供很多其他声音，
# 可以运行 `edge-tts --list-voices` 查看完整列表，换个名字就能换声音。
VOICE = "en-US-AriaNeural"


async def synthesize_speech(text: str) -> bytes:
    """
    把文字转成 mp3 格式的语音字节流。

    参数：
        text: 要朗读的文字（建议提前去掉 💡 Tip 部分，避免把纠错提示也读出来）

    返回：
        mp3 音频的字节内容，可以直接返回给前端播放
    """
    communicate = edge_tts.Communicate(text, VOICE)

    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])

    return audio_buffer.getvalue()
