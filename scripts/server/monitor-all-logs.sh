#!/bin/bash
# ============================================================
# 监控所有服务日志
# ============================================================
# 功能：实时监控后端和 Bot 的所有日志
# 使用方法：bash scripts/server/monitor-all-logs.sh
# ============================================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务名称
BACKEND_SERVICE="telegram-backend"
BOT_SERVICE="telegram-bot"

echo "============================================================"
echo "📋 实时监控所有服务日志"
echo "============================================================"
echo ""
echo -e "${YELLOW}提示: 按 Ctrl+C 退出监控${NC}"
echo ""

# 使用 journalctl 同时监控多个服务
sudo journalctl -u "$BACKEND_SERVICE" -u "$BOT_SERVICE" -f --no-pager

