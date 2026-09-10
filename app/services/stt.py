"""
STT（Speech-to-Text，语音转文字）服务。
用的是 OpenAI 的 Whisper API，直接把浏览器录的音频文件发过去就行，
不需要自己做格式转换（Whisper API 原生支持 webm/mp3/wav 等常见格式）。
"""
from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


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
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes),
        language="en",  # 明确告诉模型是英语，识别准确率会更高
    )
    return transcript.text.strip()
