#!/bin/bash
# ============================================================
# 修复端口 8000 占用问题
# ============================================================
# 功能：停止占用端口 8000 的进程，然后重启服务
# 使用方法：sudo bash scripts/server/fix-port-8000.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "🔧 修复端口 8000 占用问题"
echo "============================================================"
echo ""

# 检查端口占用
echo "[1] 检查端口 8000 占用情况..."
PORT_PID=$(ss -tlnp | grep ':8000' | grep -oP 'pid=\K[0-9]+' | head -1 || echo "")

if [ -n "$PORT_PID" ]; then
    echo -e "  ${YELLOW}⚠️  端口 8000 被进程 $PORT_PID 占用${NC}"
    echo "  进程信息:"
    ps -p "$PORT_PID" -o pid,user,cmd || true
    echo ""
    echo "  停止占用端口的进程..."
    kill -9 "$PORT_PID" 2>/dev/null || true
    sleep 2
    echo -e "  ${GREEN}✅ 进程已停止${NC}"
else
    echo -e "  ${GREEN}✅ 端口 8000 未被占用${NC}"
fi
echo ""

# 停止服务
echo "[2] 停止 luckyred-api 服务..."
sudo systemctl stop luckyred-api 2>/dev/null || true
sleep 2
echo -e "  ${GREEN}✅ 服务已停止${NC}"
echo ""

# 再次检查端口
echo "[3] 再次检查端口 8000..."
if ss -tlnp | grep -q ':8000'; then
    echo -e "  ${RED}❌ 端口 8000 仍被占用${NC}"
    echo "  强制停止所有 uvicorn 进程..."
    pkill -9 -f "uvicorn.*8000" || true
    sleep 2
else
    echo -e "  ${GREEN}✅ 端口 8000 已释放${NC}"
fi
echo ""

# 重新加载 systemd
echo "[4] 重新加载 systemd..."
sudo systemctl daemon-reload
echo -e "  ${GREEN}✅ Systemd 已重新加载${NC}"
echo ""

# 启动服务
echo "[5] 启动 luckyred-api 服务..."
sudo systemctl start luckyred-api
sleep 3
echo ""

# 检查服务状态
echo "[6] 检查服务状态..."
if systemctl is-active --quiet luckyred-api; then
    echo -e "  ${GREEN}✅ 服务已启动${NC}"
else
    echo -e "  ${RED}❌ 服务启动失败${NC}"
    echo "  查看日志:"
    sudo journalctl -u luckyred-api -n 20 --no-pager || true
fi
echo ""

# 检查端口监听
echo "[7] 检查端口监听..."
if ss -tlnp | grep -q ':8000'; then
    echo -e "  ${GREEN}✅ 端口 8000 正在监听${NC}"
    ss -tlnp | grep ':8000' | awk '{print "    " $0}'
else
    echo -e "  ${YELLOW}⚠️  端口 8000 未监听${NC}"
fi
echo ""

echo "============================================================"
echo -e "${GREEN}✅ 修复完成${NC}"
echo "============================================================"

