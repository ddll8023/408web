#!/bin/zsh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
PORT=5174

if [[ ! -d "$FRONTEND_DIR" || ! -f "$FRONTEND_DIR/package.json" ]]; then
  echo "[ERROR] 未找到前端项目目录或 package.json：$FRONTEND_DIR"
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "[ERROR] 未找到 Node.js，请先安装 Node.js。"
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "[ERROR] 未找到 node_modules，请先在 frontend 目录执行 npm install。"
  exit 1
fi

echo "============================================"
echo "  408Web 前端开发服务器"
echo "  访问地址：http://localhost:$PORT"
echo "============================================"
echo "Node.js 版本：$(node --version)"
echo "按 Ctrl+C 停止服务"
echo

cd "$FRONTEND_DIR"
exec npm run dev
