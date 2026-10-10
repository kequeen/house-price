#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys; assert sys.version_info >= (3,10), "需要Python 3.10+"'
node -e 'if (Number(process.versions.node.split(".")[0]) < 18) throw new Error("需要Node.js 18+")'
if [ ! -d backend/.venv ]; then python3 -m venv backend/.venv; fi
backend/.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm ci)
echo "依赖安装完成，运行 ./start.sh；官方数据可在页面或sync_official.py中同步。"
