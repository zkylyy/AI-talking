# English Speaking AI（英语口语对话 AI）

一个最小可用的英语口语陪练 Demo：浏览器录音 → 语音识别（STT）→ AI 对话（LLM）→ 语音合成（TTS）→ 浏览器播放。

## 架构

```
浏览器（static/index.html，录音+播放）
        │  HTTP POST 音频文件
        ▼
FastAPI 后端（app/main.py）
        │
        ├─ STT：OpenAI Whisper API   （app/services/stt.py）
        ├─ LLM：Anthropic Claude API （app/services/llm.py）
        └─ TTS：edge-tts（免费，无需 API Key）（app/services/tts.py）
```

## 本地运行

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

3. 启动服务：

```bash
uvicorn app.main:app --reload --port 8080
```

4. 浏览器打开 `http://localhost:8080` 即可开始对话。

> 注意：麦克风录音需要 HTTPS 或 localhost 环境，浏览器才会允许调用麦克风权限。

## 部署到 Google Cloud Run

```bash
# 1. 构建并推送镜像（PROJECT_ID 换成你自己的项目ID）
gcloud builds submit --tag gcr.io/PROJECT_ID/english-speaking-ai

# 2. 部署到 Cloud Run，并把 API Key 作为环境变量传入
gcloud run deploy english-speaking-ai \
  --image gcr.io/PROJECT_ID/english-speaking-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=你的key,OPENAI_API_KEY=你的key

# 3. （可选）绑定自定义域名
gcloud beta run domain-mappings create \
  --service english-speaking-ai \
  --domain your-domain.com \
  --region us-central1
```

## 目前是最简版本，还没做的事（放到 GitHub 前建议知道）

- **对话历史目前存在内存里**（见 `main.py` 里的 `SESSIONS` 字典）。Cloud Run 会根据流量自动开多个实例，
  内存数据不共享，用户可能这次连到实例A、下次连到实例B，导致"AI 忘记上下文"。
  生产环境建议换成 Redis / Firestore 这类外部存储。
- **没有做鉴权和限流**，任何人拿到你的域名都能调用，会消耗你的 API 额度。正式上线前建议加一个简单的
  API Key 校验或者接入 Cloudflare 的速率限制。
- **TTS 用的 edge-tts 是免费的非官方接口**（微软没有正式开放这个协议），稳定性不如付费 API，
  如果后续要做商用建议换成 OpenAI TTS 或 Azure 官方语音服务。
