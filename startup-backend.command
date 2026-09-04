#!/bin/zsh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend-fastapi"
PYTHON="$BACKEND_DIR/.venv/bin/python"
PORT=8081

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "[ERROR] 未找到后端项目目录：$BACKEND_DIR"
  exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "[ERROR] 未找到后端虚拟环境，请先创建 $BACKEND_DIR/.venv 并安装依赖。"
  exit 1
fi

echo "============================================"
echo "  408Web FastAPI 后端服务"
echo "  服务地址：http://localhost:$PORT"
echo "  API 文档：http://localhost:$PORT/docs"
echo "============================================"
echo "Python 版本：$($PYTHON --version)"
echo "按 Ctrl+C 停止服务"
echo

cd "$BACKEND_DIR"
exec "$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
