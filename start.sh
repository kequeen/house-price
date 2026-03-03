#!/bin/bash

echo "=== 房价分析系统启动脚本 ==="

cd "$(dirname "$0")"

if [ ! -d "backend/.venv" ]; then
    echo "创建Python虚拟环境..."
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

echo "启动后端服务..."
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 3

echo "检查前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "启动前端服务..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=== 服务已启动 ==="
echo "后端API: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "前端界面: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

wait
