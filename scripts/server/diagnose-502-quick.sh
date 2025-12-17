#!/bin/bash
# 快速诊断 502 错误

echo "========================================="
echo "快速诊断 502 Bad Gateway 错误"
echo "========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

# 1. 检查后端服务
echo "[1/4] 检查后端服务状态..."
if sudo systemctl is-active --quiet luckyred-api; then
    success_msg "后端服务正在运行"
else
    error_msg "后端服务未运行！"
    echo "查看后端服务状态："
    sudo systemctl status luckyred-api --no-pager | head -15
    echo ""
    echo "查看后端错误日志："
    sudo journalctl -u luckyred-api -n 30 --no-pager
fi
echo ""

# 2. 检查前端服务
echo "[2/4] 检查前端服务状态..."
if sudo systemctl is-active --quiet liaotian-frontend; then
    success_msg "前端服务正在运行"
else
    error_msg "前端服务未运行！"
    echo "查看前端服务状态："
    sudo systemctl status liaotian-frontend --no-pager | head -15
    echo ""
    echo "查看前端错误日志："
    sudo journalctl -u liaotian-frontend -n 30 --no-pager
fi
echo ""

# 3. 检查端口监听
echo "[3/4] 检查端口监听..."
echo "端口 8000 (后端):"
if sudo ss -tlnp | grep -q ":8000 "; then
    success_msg "端口 8000 正在监听"
    sudo ss -tlnp | grep ":8000"
else
    error_msg "端口 8000 未监听（后端服务可能未运行）"
fi

echo ""
echo "端口 3000 (前端):"
if sudo ss -tlnp | grep -q ":3000 "; then
    success_msg "端口 3000 正在监听"
    sudo ss -tlnp | grep ":3000"
else
    error_msg "端口 3000 未监听（前端服务可能未运行）"
fi
echo ""

# 4. 检查 Nginx
echo "[4/4] 检查 Nginx 状态..."
if sudo systemctl is-active --quiet nginx; then
    success_msg "Nginx 正在运行"
    echo ""
    echo "Nginx 错误日志（最近10行）："
    sudo tail -10 /var/log/nginx/error.log
else
    error_msg "Nginx 未运行！"
    sudo systemctl status nginx --no-pager | head -10
fi
echo ""

# 5. 快速修复建议
echo "========================================="
echo "快速修复建议"
echo "========================================="
echo ""

if ! sudo systemctl is-active --quiet luckyred-api; then
    echo "🔧 启动后端服务："
    echo "   sudo systemctl start luckyred-api"
    echo "   sudo systemctl status luckyred-api"
    echo ""
fi

if ! sudo systemctl is-active --quiet liaotian-frontend; then
    echo "🔧 启动前端服务："
    echo "   sudo systemctl start liaotian-frontend"
    echo "   sudo systemctl status liaotian-frontend"
    echo ""
fi

echo "🔧 重启所有服务："
echo "   sudo systemctl restart luckyred-api liaotian-frontend nginx"
echo ""
echo "🔧 查看实时日志："
echo "   后端: sudo journalctl -u luckyred-api -f"
echo "   前端: sudo journalctl -u liaotian-frontend -f"
echo "   Nginx: sudo tail -f /var/log/nginx/error.log"
echo ""
