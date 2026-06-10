# ---- 构建阶段 ----
FROM python:3.11-slim AS builder

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- 运行阶段 ----
FROM python:3.11-slim

WORKDIR /app

# 安全: 创建非 root 用户
RUN groupadd -r oa && useradd -r -g oa oa

# 从构建阶段复制依赖
COPY --from=builder /root/.local /home/oa/.local

# 复制应用代码
COPY backend/ .

# 创建必要目录
RUN mkdir -p /app/data /app/logs /app/chroma_db_knowledge && \
    chown -R oa:oa /app

# 设置环境变量
ENV PATH=/home/oa/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER oa

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
