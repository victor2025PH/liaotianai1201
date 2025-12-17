#!/bin/bash
# 快速修复前端路径问题（无需 git pull）

set -e

FRONTEND_DIR="/home/ubuntu/telegram-ai-system/saas-demo"
SERVICE_FILE="/etc/systemd/system/liaotian-frontend.service"

echo "========================================="
echo "快速修复前端服务路径"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }

# 步骤 1: 查找实际的 server.js 文件
echo "[1/3] 查找 server.js 文件..."
cd "$FRONTEND_DIR" || { error_msg "无法进入前端目录"; exit 1; }

# 查找所有可能的 server.js 位置
FOUND_PATH=""
for path in ".next/standalone/server.js" ".next/standalone/saas-demo/server.js" ".next/server.js"; do
    if [ -f "$path" ]; then
        FOUND_PATH="$path"
        success_msg "找到 server.js: $path"
        break
    fi
done

if [ -z "$FOUND_PATH" ]; then
    error_msg "未找到 server.js 文件！"
    echo "搜索所有可能的 server.js 文件..."
    find .next -name "server.js" -type f 2>/dev/null || echo "未找到任何 server.js 文件"
    exit 1
fi

echo ""

# 步骤 2: 修复服务配置文件
echo "[2/3] 修复服务配置文件..."
ABSOLUTE_PATH="$FRONTEND_DIR/$FOUND_PATH"
info_msg "使用路径: $ABSOLUTE_PATH"

# 备份原文件
sudo cp "$SERVICE_FILE" "$SERVICE_FILE.bak" 2>/dev/null || true

# 修复 ExecStart 行（使用绝对路径）
sudo sed -i "s|ExecStart=.*node.*server\.js|ExecStart=/usr/bin/node $ABSOLUTE_PATH|" "$SERVICE_FILE"

# 验证修复
NEW_EXECSTART=$(grep "ExecStart=" "$SERVICE_FILE")
success_msg "服务配置已更新"
echo "新的配置: $NEW_EXECSTART"
echo ""

# 步骤 3: 重新加载并重启服务
echo "[3/3] 重新加载并重启服务..."
sudo systemctl daemon-reload
sudo systemctl stop liaotian-frontend 2>/dev/null || true
sleep 2
sudo systemctl start liaotian-frontend
sleep 5

# 检查服务状态
if sudo systemctl is-active --quiet liaotian-frontend; then
    success_msg "前端服务已成功启动！"
    echo ""
    sudo systemctl status liaotian-frontend --no-pager | head -10
else
    error_msg "前端服务启动失败"
    echo ""
    echo "查看错误日志:"
    sudo journalctl -u liaotian-frontend -n 20 --no-pager
    exit 1
fi

echo ""
echo "========================================="
echo "修复完成！"
echo "========================================="
