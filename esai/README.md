# English Speaking AI

浏览器录音 → Whisper 识别 → Claude 回复 → edge-tts 朗读 → 浏览器播放。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # 然后编辑 .env，填入两个 API Key
python -m uvicorn app.main:app --reload --port 8080
```

浏览器打开 http://localhost:8080 ，点按钮说英语即可。

## API Key（三种方案，填一种即可）

优先级：GEMINI > GROQ > ANTHROPIC+OPENAI。

**方案 1：Google Gemini（免费，推荐）**
用 Google 账号打开 https://aistudio.google.com/apikey 创建 Key，无需绑卡。
语音识别和对话都走 Gemini。注意：免费额度下 Google 可能用你的内容改进其产品；
部分地区不支持 Gemini API，会提示 "location is not supported"。

**方案 2：Groq（免费）**
https://console.groq.com/keys ，部分网络环境注册会被风控。

**方案 3：付费，回复质量最好**
ANTHROPIC_API_KEY（https://console.anthropic.com/）+ OPENAI_API_KEY（https://platform.openai.com/api-keys），都需要先充值。

## 部署到 Cloud Run

```bash
gcloud config set project 你的项目ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com

printf "你的Gemini key" | gcloud secrets create gemini-key --data-file=-
printf "自己想一个口令"   | gcloud secrets create access-token --data-file=-

gcloud run deploy english-speaking-ai \
  --source . \
  --region us-central1 \
  --max-instances 2 \
  --allow-unauthenticated \
  --set-secrets GEMINI_API_KEY=gemini-key:latest,ACCESS_TOKEN=access-token:latest
```

如果提示权限不足，把 Secret Accessor 角色授予 Cloud Run 使用的服务账号后重试。
设置了 ACCESS_TOKEN 后，第一次打开页面会要求输入口令，防止别人刷你的额度。

（用其他方案的话，把 secret 和环境变量名换成对应的 Key。）

## 设计说明

- 对话历史保存在浏览器里，每次请求带给后端，后端无状态，缩容/多实例都不会丢上下文。
- TTS 失败时只返回文字，不影响对话。
- edge-tts 是非官方接口，可能随时失效；商用请换官方 TTS。
