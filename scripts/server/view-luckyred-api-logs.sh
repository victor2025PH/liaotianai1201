#!/bin/bash
# ============================================================
# 查看 luckyred-api 服务的详细错误日志
# ============================================================
# 功能：显示服务的详细错误信息，帮助诊断启动失败的原因
# 使用方法：bash scripts/server/view-luckyred-api-logs.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "📋 查看 luckyred-api 服务详细日志"
echo "============================================================"
echo ""

# 1. 服务状态
echo "[1] 服务状态:"
sudo systemctl status luckyred-api --no-pager -l | head -30
echo ""

# 2. 最近的错误日志（最后 50 行）
echo "[2] 最近的错误日志（最后 50 行）:"
echo "============================================================"
sudo journalctl -u luckyred-api -n 50 --no-pager --no-hostname
echo ""

# 3. 只显示错误和警告
echo "[3] 错误和警告日志:"
echo "============================================================"
sudo journalctl -u luckyred-api --no-pager --no-hostname | grep -iE "error|warning|failed|exception|traceback" | tail -30 || echo "  没有找到错误或警告"
echo ""

# 4. 尝试手动启动以查看实时错误
echo "[4] 尝试手动启动（查看实时错误）:"
echo "============================================================"
echo "  执行命令: cd /home/ubuntu/telegram-ai-system/admin-backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  注意：这将占用当前终端，按 Ctrl+C 停止"
echo ""
read -p "  是否执行手动启动测试？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd /home/ubuntu/telegram-ai-system/admin-backend
    source venv/bin/activate
    echo "  开始手动启动..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000
fi

echo ""
echo "============================================================"

