#!/bin/bash
# 启动后端API服务器

cd "$(dirname "$0")"
export PYTHONPATH=$(pwd)

# 检查端口
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口8000已被占用,尝试停止旧进程..."
    pkill -f "uvicorn apps.api_gateway.main" || true
    sleep 2
fi

echo "🚀 启动FastAPI后端服务器..."
python3 -m uvicorn apps.api_gateway.main:app --reload --host 0.0.0.0 --port 8000
