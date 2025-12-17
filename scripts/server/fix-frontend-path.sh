#!/bin/bash
# 修复前端服务路径问题

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
SERVICE_FILE="/etc/systemd/system/liaotian-frontend.service"

echo "========================================="
echo "修复前端服务路径"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

info_msg() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

error_msg() {
    echo -e "${RED}❌ $1${NC}"
}

# 步骤 1: 查找实际的 server.js 文件
echo "[1/4] 查找 server.js 文件位置..."
cd "$FRONTEND_DIR"

# 查找所有可能的 server.js 位置
SERVER_JS_PATHS=(
    ".next/standalone/server.js"
    ".next/standalone/saas-demo/server.js"
    ".next/server.js"
)

FOUND_PATH=""
for path in "${SERVER_JS_PATHS[@]}"; do
    if [ -f "$path" ]; then
        FOUND_PATH="$path"
        success_msg "找到 server.js: $path"
        ls -lh "$path"
        break
    fi
done

if [ -z "$FOUND_PATH" ]; then
    error_msg "未找到 server.js 文件！"
    echo "正在搜索所有可能的 server.js 文件..."
    find .next -name "server.js" -type f 2>/dev/null || echo "未找到任何 server.js 文件"
    echo ""
    error_msg "请先构建前端: cd $FRONTEND_DIR && npm run build"
    exit 1
fi

echo ""

# 步骤 2: 修复服务配置文件
echo "[2/4] 修复服务配置文件..."

# 检查服务文件是否存在
if [ ! -f "$SERVICE_FILE" ]; then
    error_msg "服务文件不存在: $SERVICE_FILE"
    exit 1
fi

# 获取当前配置的路径
CURRENT_PATH=$(grep "ExecStart=" "$SERVICE_FILE" | sed 's/.*\.next\/\([^ ]*\).*/.next\/\1/' | head -1)
info_msg "当前配置路径: $CURRENT_PATH"
info_msg "实际文件路径: $FOUND_PATH"

# 修复路径（使用绝对路径以确保正确）
ABSOLUTE_PATH="$FRONTEND_DIR/$FOUND_PATH"
info_msg "使用绝对路径: $ABSOLUTE_PATH"

# 备份原文件
sudo cp "$SERVICE_FILE" "$SERVICE_FILE.bak"
info_msg "已备份服务文件到: $SERVICE_FILE.bak"

# 修复 ExecStart 行
sudo sed -i "s|ExecStart=.*server\.js|ExecStart=/usr/bin/node $ABSOLUTE_PATH|" "$SERVICE_FILE"

# 验证修复
NEW_PATH=$(grep "ExecStart=" "$SERVICE_FILE")
success_msg "服务配置已更新"
echo "新的 ExecStart: $NEW_PATH"
echo ""

# 步骤 3: 重新加载 systemd
echo "[3/4] 重新加载 systemd..."
sudo systemctl daemon-reload
success_msg "systemd 已重新加载"
echo ""

# 步骤 4: 重启前端服务
echo "[4/4] 重启前端服务..."
sudo systemctl stop liaotian-frontend 2>/dev/null || true
sleep 2
sudo systemctl start liaotian-frontend
sleep 5

# 检查服务状态
if sudo systemctl is-active --quiet liaotian-frontend; then
    success_msg "前端服务已成功启动！"
    echo ""
    echo "服务状态:"
    sudo systemctl status liaotian-frontend --no-pager | head -10
    echo ""
    echo "端口监听:"
    sudo ss -tlnp | grep :3000 || echo "端口 3000 尚未监听，等待服务完全启动..."
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
