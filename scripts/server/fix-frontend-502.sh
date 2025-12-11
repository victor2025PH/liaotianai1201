#!/bin/bash
# ============================================================
# 修复前端 502 错误脚本
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "◆ 修复前端 502 错误"
echo "============================================================"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}▲ 提示：某些命令需要 sudo 权限${NC}"
    SUDO="sudo"
else
    SUDO=""
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
SERVICE_NAME="liaotian-frontend"

echo "[1] 停止前端服务..."
echo "----------------------------------------"
$SUDO systemctl stop "$SERVICE_NAME" 2>/dev/null || true
echo -e "${GREEN}□ 服务已停止${NC}"
echo ""

echo "[2] 检查前端构建目录..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || {
    echo -e "${RED}❌ 无法进入前端目录: $FRONTEND_DIR${NC}"
    exit 1
}

if [ ! -d ".next/standalone" ]; then
    echo -e "${RED}❌ .next/standalone 目录不存在，需要重新构建${NC}"
    echo "  执行: cd $FRONTEND_DIR && npm run build"
    exit 1
fi

echo -e "${GREEN}□ .next/standalone 目录存在${NC}"
echo ""

echo "[3] 准备 standalone 目录..."
echo "----------------------------------------"
cd "$FRONTEND_DIR/.next/standalone" || {
    echo -e "${RED}❌ 无法进入 standalone 目录${NC}"
    exit 1
}

# 复制 public 目录
if [ -d "$FRONTEND_DIR/public" ]; then
    echo "复制 public 目录..."
    cp -r "$FRONTEND_DIR/public" . || true
    echo -e "${GREEN}□ public 目录已复制${NC}"
fi

# 创建 .next 目录并复制 static
mkdir -p .next
if [ -d "$FRONTEND_DIR/.next/static" ]; then
    echo "复制 .next/static 目录..."
    cp -r "$FRONTEND_DIR/.next/static" .next/ || true
    echo -e "${GREEN}□ .next/static 目录已复制${NC}"
fi

# 检查 server.js 是否存在
if [ ! -f "server.js" ]; then
    echo -e "${RED}❌ server.js 文件不存在${NC}"
    exit 1
fi

echo -e "${GREEN}□ server.js 文件存在${NC}"
echo ""

echo "[4] 检查服务配置..."
echo "----------------------------------------"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}❌ 服务文件不存在: $SERVICE_FILE${NC}"
    exit 1
fi

# 检查 WorkingDirectory 是否正确
WORKING_DIR=$(grep "^WorkingDirectory=" "$SERVICE_FILE" | cut -d'=' -f2)
if [ "$WORKING_DIR" != "$FRONTEND_DIR/.next/standalone" ]; then
    echo -e "${YELLOW}▲ WorkingDirectory 不匹配，当前: $WORKING_DIR${NC}"
    echo "  应该为: $FRONTEND_DIR/.next/standalone"
    echo "  正在修复..."
    $SUDO sed -i "s|^WorkingDirectory=.*|WorkingDirectory=$FRONTEND_DIR/.next/standalone|g" "$SERVICE_FILE"
    $SUDO systemctl daemon-reload
    echo -e "${GREEN}□ 服务配置已更新${NC}"
fi

echo -e "${GREEN}□ 服务配置正确${NC}"
echo ""

echo "[5] 测试手动启动（查看实时错误）..."
echo "----------------------------------------"
cd "$FRONTEND_DIR/.next/standalone" || exit 1

echo "尝试手动启动 Node.js 服务器（5秒超时）..."
timeout 5s node server.js 2>&1 || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo -e "${GREEN}□ 服务器启动成功（5秒内未崩溃）${NC}"
    else
        echo -e "${RED}❌ 服务器启动失败，退出码: $EXIT_CODE${NC}"
        echo "  查看上面的错误信息"
        echo ""
        echo "  如果看到 'location is not defined' 错误，说明代码修复未生效"
        echo "  请检查："
        echo "    1. 代码是否已更新: cd $FRONTEND_DIR && git log -1"
        echo "    2. 是否重新构建: npm run build"
        echo "    3. standalone 目录是否是最新的"
    fi
}
echo ""

echo "[6] 启动前端服务..."
echo "----------------------------------------"
$SUDO systemctl start "$SERVICE_NAME"
sleep 3

STATUS=$($SUDO systemctl is-active "$SERVICE_NAME" 2>/dev/null | awk 'NR==1 {print $1}' || echo "inactive")
if [ "$STATUS" = "active" ]; then
    echo -e "${GREEN}□ 服务已启动${NC}"
else
    echo -e "${RED}❌ 服务启动失败，状态: $STATUS${NC}"
    echo "  查看日志: sudo journalctl -u $SERVICE_NAME -n 30 --no-pager"
    exit 1
fi
echo ""

echo "[7] 等待服务稳定（10秒）..."
echo "----------------------------------------"
sleep 10

# 再次检查状态
STATUS=$($SUDO systemctl is-active "$SERVICE_NAME" 2>/dev/null | awk 'NR==1 {print $1}' || echo "inactive")
if [ "$STATUS" != "active" ]; then
    echo -e "${RED}❌ 服务在启动后崩溃，状态: $STATUS${NC}"
    echo "  查看日志: sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
    exit 1
fi
echo ""

echo "[8] 检查端口监听..."
echo "----------------------------------------"
PORT_3000=$(sudo ss -tlnp | grep ":3000" || echo "")
if [ -n "$PORT_3000" ]; then
    echo -e "${GREEN}□ 端口 3000 正在监听${NC}"
    echo "  $PORT_3000"
else
    echo -e "${RED}❌ 端口 3000 未监听${NC}"
    echo "  服务可能仍在崩溃循环中"
    echo "  查看日志: sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
    exit 1
fi
echo ""

echo "[9] 测试前端连接..."
echo "----------------------------------------"
if timeout 5s curl -s -f http://localhost:3000 >/dev/null 2>&1; then
    echo -e "${GREEN}□ 前端连接成功${NC}"
else
    echo -e "${YELLOW}▲ 前端连接失败，但端口正在监听${NC}"
    echo "  可能需要更多时间启动，或检查应用内部错误"
fi
echo ""

echo "============================================================"
echo -e "${GREEN}□ 修复完成${NC}"
echo "============================================================"
echo ""
echo "如果问题仍然存在，请运行："
echo "  sudo journalctl -u $SERVICE_NAME -n 100 --no-pager"
echo "  查看详细错误日志"

