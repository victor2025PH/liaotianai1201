#!/bin/bash
# ============================================================
# Systemd 自动化部署脚本
# ============================================================
# 功能：自动部署 FastAPI 后端和 Telegram Bot 的 systemd 服务
# 使用方法：sudo bash scripts/server/deploy-systemd.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量 - 自动检测实际路径和用户
# 从脚本位置推断项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"
BOT_DIR="$PROJECT_ROOT"
# 自动检测实际用户（从项目目录的所有者）
SERVICE_USER="$(stat -c '%U' "$PROJECT_ROOT" 2>/dev/null || echo "ubuntu")"
SERVICE_GROUP="$(stat -c '%G' "$PROJECT_ROOT" 2>/dev/null || echo "ubuntu")"

# Systemd 服务文件路径
SYSTEMD_DIR="/etc/systemd/system"
BACKEND_SERVICE="luckyred-api.service"
BOT_SERVICE="telegram-bot.service"

# 部署文件目录
DEPLOY_DIR="$(cd "$SCRIPT_DIR/../../deploy/systemd" && pwd)"

echo "============================================================"
echo "🚀 Systemd 服务自动化部署"
echo "============================================================"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 错误：请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 检查项目目录是否存在
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}❌ 错误：项目目录不存在: $PROJECT_ROOT${NC}"
    exit 1
fi

# 检查部署文件是否存在（优先使用 luckyred-api，否则使用 telegram-backend）
if [ ! -f "$DEPLOY_DIR/$BACKEND_SERVICE" ]; then
    # 如果 luckyred-api.service 不存在，尝试使用 telegram-backend.service
    if [ -f "$DEPLOY_DIR/telegram-backend.service" ]; then
        echo -e "${YELLOW}⚠️  使用 telegram-backend.service 作为备用${NC}"
        BACKEND_SERVICE="telegram-backend.service"
    else
        echo -e "${RED}❌ 错误：后端服务文件不存在: $DEPLOY_DIR/$BACKEND_SERVICE${NC}"
        exit 1
    fi
fi

if [ ! -f "$DEPLOY_DIR/$BOT_SERVICE" ]; then
    echo -e "${RED}❌ 错误：Bot 服务文件不存在: $DEPLOY_DIR/$BOT_SERVICE${NC}"
    exit 1
fi

echo "📋 部署配置："
echo "   项目根目录: $PROJECT_ROOT"
echo "   后端目录: $BACKEND_DIR"
echo "   Bot 目录: $BOT_DIR"
echo "   服务用户: $SERVICE_USER"
echo ""

# 步骤 1: 检查虚拟环境
echo "[1/6] 检查虚拟环境..."
if [ ! -d "$BACKEND_DIR/venv" ] && [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo -e "${YELLOW}⚠️  后端虚拟环境不存在，请先创建：${NC}"
    echo "   cd $BACKEND_DIR && python3 -m venv venv"
    exit 1
fi

if [ ! -d "$BOT_DIR/venv" ] && [ ! -d "$BOT_DIR/.venv" ]; then
    echo -e "${YELLOW}⚠️  Bot 虚拟环境不存在，请先创建：${NC}"
    echo "   cd $BOT_DIR && python3 -m venv venv"
    exit 1
fi
echo -e "${GREEN}✅ 虚拟环境检查完成${NC}"
echo ""

# 步骤 2: 停止现有服务（如果存在）
echo "[2/6] 停止现有服务..."
if systemctl is-active --quiet "$BACKEND_SERVICE" 2>/dev/null; then
    echo "   停止 $BACKEND_SERVICE..."
    systemctl stop "$BACKEND_SERVICE" || true
fi

if systemctl is-active --quiet "$BOT_SERVICE" 2>/dev/null; then
    echo "   停止 $BOT_SERVICE..."
    systemctl stop "$BOT_SERVICE" || true
fi
echo -e "${GREEN}✅ 服务已停止${NC}"
echo ""

# 步骤 3: 复制服务文件
echo "[3/6] 安装 systemd 服务文件..."
cp "$DEPLOY_DIR/$BACKEND_SERVICE" "$SYSTEMD_DIR/"
cp "$DEPLOY_DIR/$BOT_SERVICE" "$SYSTEMD_DIR/"

# 更新服务文件中的路径和用户（自动替换）
sed -i "s|/home/ubuntu/telegram-ai-system|$PROJECT_ROOT|g" "$SYSTEMD_DIR/$BACKEND_SERVICE"
sed -i "s|/home/ubuntu/telegram-ai-system|$PROJECT_ROOT|g" "$SYSTEMD_DIR/$BOT_SERVICE"
# 替换用户和组
sed -i "s|^User=.*|User=$SERVICE_USER|g" "$SYSTEMD_DIR/$BACKEND_SERVICE"
sed -i "s|^Group=.*|Group=$SERVICE_GROUP|g" "$SYSTEMD_DIR/$BACKEND_SERVICE"
sed -i "s|^User=.*|User=$SERVICE_USER|g" "$SYSTEMD_DIR/$BOT_SERVICE"
sed -i "s|^Group=.*|Group=$SERVICE_GROUP|g" "$SYSTEMD_DIR/$BOT_SERVICE"

chmod 644 "$SYSTEMD_DIR/$BACKEND_SERVICE"
chmod 644 "$SYSTEMD_DIR/$BOT_SERVICE"
echo -e "${GREEN}✅ 服务文件已安装${NC}"
echo ""

# 步骤 4: 重新加载 systemd
echo "[4/6] 重新加载 systemd..."
systemctl daemon-reload
echo -e "${GREEN}✅ Systemd 已重新加载${NC}"
echo ""

# 步骤 5: 启用服务（开机自启）
echo "[5/6] 启用服务（开机自启）..."
systemctl enable "$BACKEND_SERVICE"
systemctl enable "$BOT_SERVICE"
echo -e "${GREEN}✅ 服务已启用${NC}"
echo ""

# 步骤 6: 启动服务
echo "[6/6] 启动服务..."
echo "   启动 $BACKEND_SERVICE..."
systemctl start "$BACKEND_SERVICE"
sleep 3

echo "   启动 $BOT_SERVICE..."
systemctl start "$BOT_SERVICE"
sleep 3

# 检查服务状态
echo ""
echo "============================================================"
echo "📊 服务状态检查"
echo "============================================================"

if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo -e "${GREEN}✅ $BACKEND_SERVICE: 运行中${NC}"
else
    echo -e "${RED}❌ $BACKEND_SERVICE: 未运行${NC}"
    echo "   查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50"
fi

if systemctl is-active --quiet "$BOT_SERVICE"; then
    echo -e "${GREEN}✅ $BOT_SERVICE: 运行中${NC}"
else
    echo -e "${RED}❌ $BOT_SERVICE: 未运行${NC}"
    echo "   查看日志: sudo journalctl -u $BOT_SERVICE -n 50"
fi

echo ""
echo "============================================================"
echo "✅ 部署完成！"
echo "============================================================"
echo ""
echo "📝 常用命令："
echo "   查看后端状态: sudo systemctl status $BACKEND_SERVICE"
echo "   查看 Bot 状态: sudo systemctl status $BOT_SERVICE"
echo "   查看后端日志: sudo journalctl -u $BACKEND_SERVICE -f"
echo "   查看 Bot 日志: sudo journalctl -u $BOT_SERVICE -f"
echo "   重启后端: sudo systemctl restart $BACKEND_SERVICE"
echo "   重启 Bot: sudo systemctl restart $BOT_SERVICE"
echo ""

