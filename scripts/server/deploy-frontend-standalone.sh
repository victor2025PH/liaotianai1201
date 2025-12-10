#!/bin/bash
# ============================================================
# Deploy Frontend with Standalone Mode
# ============================================================
# 功能：部署 Next.js 前端服务（使用 standalone 模式）
# 使用方法：sudo bash scripts/server/deploy-frontend-standalone.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/saas-demo"
SERVICE_NAME="liaotian-frontend.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
NODE_VERSION="20.19.6"
NODE_PATH="/home/ubuntu/.nvm/versions/node/v$NODE_VERSION/bin/node"

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}🚀 部署 Next.js 前端服务（Standalone 模式）${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "📋 配置信息："
echo -e "   项目目录: $FRONTEND_DIR"
echo -e "   服务名称: $SERVICE_NAME"
echo -e "   Node 版本: v$NODE_VERSION"
echo ""

# 1. 检查 Node.js
echo -e "${YELLOW}[1/6] 检查 Node.js...${NC}"
if [ ! -f "$NODE_PATH" ]; then
    echo -e "   ❌ Node.js v$NODE_VERSION 未找到"
    echo -e "   请先安装: source ~/.nvm/nvm.sh && nvm install $NODE_VERSION"
    exit 1
fi
echo -e "   ✅ Node.js 已安装: $NODE_PATH"
echo ""

# 2. 进入项目目录
echo -e "${YELLOW}[2/6] 进入项目目录...${NC}"
cd "$FRONTEND_DIR"
echo -e "   ✅ 当前目录: $(pwd)"
echo ""

# 3. 安装依赖
echo -e "${YELLOW}[3/6] 安装依赖...${NC}"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use $NODE_VERSION || true
npm install --production=false
echo -e "   ✅ 依赖安装完成"
echo ""

# 4. 构建项目
echo -e "${YELLOW}[4/6] 构建项目...${NC}"
npm run build
echo -e "   ✅ 构建完成"
echo ""

# 5. 检查 standalone 文件
echo -e "${YELLOW}[5/6] 检查 standalone 文件...${NC}"
if [ ! -f "$FRONTEND_DIR/.next/standalone/server.js" ]; then
    echo -e "   ❌ standalone/server.js 不存在"
    echo -e "   请检查 next.config.ts 是否启用了 output: 'standalone'"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR/.next/static" ]; then
    echo -e "   ❌ .next/static 目录不存在"
    exit 1
fi

# 复制 static 文件到 standalone（如果需要）
if [ ! -d "$FRONTEND_DIR/.next/standalone/.next/static" ]; then
    echo -e "   ⚠️  复制 static 文件到 standalone..."
    cp -r "$FRONTEND_DIR/.next/static" "$FRONTEND_DIR/.next/standalone/.next/"
    echo -e "   ✅ static 文件已复制"
fi

echo -e "   ✅ standalone 文件检查通过"
echo ""

# 6. 安装 systemd 服务
echo -e "${YELLOW}[6/6] 安装 systemd 服务...${NC}"

# 停止现有服务
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# 复制服务文件
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
sudo cp "$SCRIPT_DIR/../systemd/$SERVICE_NAME" "$SERVICE_FILE"
sudo chmod 644 "$SERVICE_FILE"

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable "$SERVICE_NAME"

# 启动服务
sudo systemctl start "$SERVICE_NAME"

# 等待服务启动
sleep 5

# 检查服务状态
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "   ✅ 服务已启动"
else
    echo -e "   ❌ 服务启动失败"
    echo -e "   查看日志: sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
    exit 1
fi
echo ""

# 7. 验证
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}📊 验证部署${NC}"
echo -e "${GREEN}============================================================${NC}"

# 检查端口
if ss -tlnp | grep -q ":3000"; then
    echo -e "✅ 端口 3000 正在监听"
else
    echo -e "❌ 端口 3000 未监听"
fi

# 检查服务状态
SERVICE_STATUS=$(sudo systemctl is-active "$SERVICE_NAME" || echo "inactive")
if [ "$SERVICE_STATUS" == "active" ]; then
    echo -e "✅ 服务状态: 运行中"
else
    echo -e "❌ 服务状态: $SERVICE_STATUS"
fi

# 测试 HTTP 响应
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "301" ] || [ "$HTTP_CODE" == "302" ]; then
    echo -e "✅ HTTP 响应: $HTTP_CODE"
else
    echo -e "❌ HTTP 响应: $HTTP_CODE"
fi

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "📝 常用命令："
echo -e "   查看服务状态: sudo systemctl status $SERVICE_NAME"
echo -e "   查看服务日志: sudo journalctl -u $SERVICE_NAME -f"
echo -e "   重启服务: sudo systemctl restart $SERVICE_NAME"
echo -e "   停止服务: sudo systemctl stop $SERVICE_NAME"
echo ""

