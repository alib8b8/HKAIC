# Hongkun AI Chain — 节点Docker镜像
# 基于Python 3.11，纯标准库，零外部依赖

FROM python:3.11-slim

LABEL maintainer="HKC Team"
LABEL description="Hongkun AI Chain v4.0.0 Node"
LABEL version="4.0.0"

# 设置工作目录
WORKDIR /app/hongkun_ai_lab

# 复制项目文件
COPY . /app/hongkun_ai_lab/

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/hongkun_ai_lab

# 暴露端口: P2P + RPC
EXPOSE 8001-8005 8841-8845

# 健康检查
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${RPC_PORT:-8841}/p2p/ping')" || exit 1

# 默认启动节点0
ENTRYPOINT ["python", "scripts/node_process.py"]
