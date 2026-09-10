# 用轻量的 Python 官方镜像，体积小、构建快
FROM python:3.11-slim

WORKDIR /app

# 先只复制依赖文件再安装，这样只要 requirements.txt 没变，
# Docker 就能复用缓存层，重新构建时会快很多
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制其余代码
COPY app ./app
COPY static ./static

# Cloud Run 通过环境变量 PORT 告诉容器要监听哪个端口（默认是 8080）
ENV PORT=8080
EXPOSE 8080

# 用 sh -c 是为了让 $PORT 环境变量能被正确展开
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
