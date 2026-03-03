#!/bin/bash

echo "=== 安装房价分析系统依赖 ==="

cd "$(dirname "$0")"

echo "安装后端依赖..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

echo "安装前端依赖..."
cd frontend
npm install
cd ..

echo "=== 安装完成 ==="
echo "运行 ./start.sh 启动服务"
