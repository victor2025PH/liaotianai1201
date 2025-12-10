#!/bin/bash
# ============================================================
# Fix Frontend Service (Standalone Mode)
# ============================================================
# 功能：修复前端服务，使用 standalone 模式
# 使用方法：sudo bash scripts/server/fix-frontend-service.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/saas-demo"
SERVICE_NAME="liaotian-frontend.service"

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}🔧 修复前端服务（Standalone 模式）${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

# 1. 停止服务
echo -e "${YELLOW}[1/5] 停止现有服务...${NC}"
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 2
echo -e "✅ 服务已停止"
echo ""

# 2. 检查 standalone 文件
echo -e "${YELLOW}[2/5] 检查 standalone 文件...${NC}"
cd "$FRONTEND_DIR"

if [ ! -f ".next/standalone/server.js" ]; then
    echo -e "   ⚠️  standalone/server.js 不存在，需要重新构建..."
    
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    nvm use 20.19.6 || true
    
    echo -e "   📋 重新构建..."
    npm run build
    
    if [ ! -f ".next/standalone/server.js" ]; then
        echo -e "   ❌ 构建后仍不存在 standalone/server.js"
        echo -e "   请检查 next.config.ts 是否启用了 output: 'standalone'"
        exit 1
    fi
fi

# 复制 static 文件（如果需要）
if [ ! -d ".next/standalone/.next/static" ]; then
    echo -e "   ⚠️  复制 static 文件到 standalone..."
    cp -r .next/static .next/standalone/.next/
fi

echo -e "✅ standalone 文件检查通过"
echo ""

# 3. 安装 systemd 服务
echo -e "${YELLOW}[3/5] 安装 systemd 服务...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo cp "$SCRIPT_DIR/../systemd/$SERVICE_NAME" "/etc/systemd/system/$SERVICE_NAME"
sudo chmod 644 "/etc/systemd/system/$SERVICE_NAME"
sudo systemctl daemon-reload
echo -e "✅ 服务文件已安装"
echo ""

# 4. 启动服务
echo -e "${YELLOW}[4/5] 启动服务...${NC}"
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"
sleep 5
echo -e "✅ 服务已启动"
echo ""

# 5. 验证
echo -e "${YELLOW}[5/5] 验证服务...${NC}"

# 检查服务状态
SERVICE_STATUS=$(sudo systemctl is-active "$SERVICE_NAME" || echo "inactive")
if [ "$SERVICE_STATUS" == "active" ]; then
    echo -e "✅ 服务状态: 运行中"
else
    echo -e "❌ 服务状态: $SERVICE_STATUS"
    echo -e "   查看日志: sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
fi

# 检查端口
if ss -tlnp | grep -q ":3000"; then
    echo -e "✅ 端口 3000 正在监听"
else
    echo -e "❌ 端口 3000 未监听"
fi

# 测试 HTTP
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "301" ] || [ "$HTTP_CODE" == "302" ]; then
    echo -e "✅ HTTP 响应: $HTTP_CODE"
else
    echo -e "❌ HTTP 响应: $HTTP_CODE"
fi

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}✅ 修复完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""

