#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
export BACKEND_PORT

if [ ! -x backend/.venv/bin/uvicorn ] || [ ! -f frontend/node_modules/vite/bin/vite.js ]; then
  echo "缺少依赖，请先运行 ./install.sh"
  exit 1
fi

BACKEND_PID=""
FRONTEND_PID=""
cleanup() {
  if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
  if [ -n "$FRONTEND_PID" ]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM

(cd backend && exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT") &
BACKEND_PID=$!

for attempt in {1..40}; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "后端启动失败，请检查端口或配置。"
    exit 1
  fi
  if curl --silent --fail "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null; then break; fi
  sleep 0.25
done
if ! curl --silent --fail "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null; then
  echo "后端未通过健康检查。"
  exit 1
fi

(cd frontend && exec node node_modules/vite/bin/vite.js --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort) &
FRONTEND_PID=$!
sleep 1
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "前端启动失败，请检查端口。"
  exit 1
fi
echo "城市住宅观察：http://127.0.0.1:$FRONTEND_PORT"
echo "API文档：http://127.0.0.1:$BACKEND_PORT/docs"
echo "按 Ctrl+C 停止前后端服务。"
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do sleep 1; done
echo "服务已停止。"
