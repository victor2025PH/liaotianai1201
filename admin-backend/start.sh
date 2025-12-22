#!/bin/bash
# ============================================================
# 后端服务启动脚本
# 用于 PM2 启动 FastAPI 应用
# ============================================================

# 获取脚本所在目录（admin-backend）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 显式设置 Python 路径，防止环境错乱
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# 启动 uvicorn
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
