"""
STT（Speech-to-Text，语音转文字）服务。
用的是 OpenAI 的 Whisper API，直接把浏览器录的音频文件发过去就行，
不需要自己做格式转换（Whisper API 原生支持 webm/mp3/wav 等常见格式）。
"""
from openai import OpenAI
from app.config import OPENAI_API_KEY

# 注意：这里不在模块加载时就创建 client，而是用到的时候才创建（见下面的 _get_client）。
# 原因：如果 OPENAI_API_KEY 没配置对，某些版本的 SDK 会在 OpenAI(...) 这一步直接抛异常，
# 而模块加载发生在程序刚启动、还没开始监听端口的阶段，会导致整个容器直接启动失败退出，
# 在 Cloud Run 上表现为 "container failed to start and listen on port" 这种不好排查的报错。
# 改成延迟初始化后，即使 key 没配对，程序也能正常启动，只有真正调用语音识别功能时才会报错，
# 报错信息也会更明确（在 API 请求的响应里能直接看到），方便定位问题。
_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    把音频字节流转成英文文字。

    参数：
        audio_bytes: 音频文件的原始字节内容
        filename: 文件名，主要是让 Whisper API 通过扩展名判断音频格式

    返回：
        识别出的英文文本（string）
    """
    # OpenAI SDK 要求传一个"类文件对象"，这里用元组 (文件名, 字节内容) 的方式传入，
    # 这样就不用先把音频落盘到磁盘再读取，节省一次磁盘 IO。
    transcript = _get_client().audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes),
        language="en",  # 明确告诉模型是英语，识别准确率会更高
    )
    return transcript.text.strip()
