#!/bin/bash
# ============================================================
# 修复前端 404 错误脚本
# ============================================================
# 功能：检查并修复前端静态资源 404 问题
# 使用方法：sudo bash scripts/server/fix-frontend-404.sh
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/saas-demo"

echo "============================================================"
echo "🔧 修复前端 404 错误"
echo "============================================================"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 错误：请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 步骤 1: 检查前端目录
echo "[1/6] 检查前端目录..."
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ 前端目录不存在: $FRONTEND_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 前端目录存在${NC}"
echo ""

# 步骤 2: 检查 .next 构建目录
echo "[2/6] 检查构建文件..."
if [ ! -d "$FRONTEND_DIR/.next" ]; then
    echo -e "${YELLOW}⚠️  .next 目录不存在，需要重新构建${NC}"
    NEED_BUILD=true
else
    echo -e "${GREEN}✅ .next 目录存在${NC}"
    NEED_BUILD=false
fi
echo ""

# 步骤 3: 停止前端服务
echo "[3/6] 停止前端服务..."
# 检查是否有 systemd 服务
if systemctl list-units --type=service | grep -q "liaotian-frontend\|smart-tg-frontend\|telegram-frontend"; then
    FRONTEND_SERVICE=$(systemctl list-units --type=service | grep -E "liaotian-frontend|smart-tg-frontend|telegram-frontend" | awk '{print $1}' | head -n 1)
    if systemctl is-active --quiet "$FRONTEND_SERVICE" 2>/dev/null; then
        echo "   停止 $FRONTEND_SERVICE..."
        systemctl stop "$FRONTEND_SERVICE" || true
    fi
fi

# 停止所有可能的 Node.js 进程
pkill -f "next.*start" 2>/dev/null || true
pkill -f "node.*3000" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅ 前端服务已停止${NC}"
echo ""

# 步骤 4: 清理旧的构建文件
echo "[4/6] 清理旧的构建文件..."
cd "$FRONTEND_DIR"
rm -rf .next 2>/dev/null || true
rm -rf node_modules/.cache 2>/dev/null || true
echo -e "${GREEN}✅ 清理完成${NC}"
echo ""

# 步骤 5: 重新构建前端
echo "[5/6] 重新构建前端..."
echo "   这可能需要几分钟，请耐心等待..."

# 设置内存限制避免 OOM
export NODE_OPTIONS="--max-old-space-size=1536"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "   安装依赖..."
    npm install
fi

# 构建
echo "   开始构建..."
npm run build

if [ -d ".next" ]; then
    echo -e "${GREEN}✅ 构建成功${NC}"
else
    echo -e "${RED}❌ 构建失败，.next 目录未创建${NC}"
    exit 1
fi
echo ""

# 步骤 6: 重启前端服务
echo "[6/6] 重启前端服务..."

# 检查是否有 systemd 服务
if [ -n "$FRONTEND_SERVICE" ]; then
    echo "   启动 $FRONTEND_SERVICE..."
    systemctl start "$FRONTEND_SERVICE"
    sleep 3
    
    if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
        echo -e "${GREEN}✅ 前端服务已启动${NC}"
    else
        echo -e "${YELLOW}⚠️  前端服务启动失败，尝试手动启动...${NC}"
        # 手动启动作为后备
        cd "$FRONTEND_DIR"
        nohup npm start > /tmp/frontend.log 2>&1 &
        sleep 3
        if pgrep -f "next.*start" > /dev/null; then
            echo -e "${GREEN}✅ 前端服务已手动启动${NC}"
        else
            echo -e "${RED}❌ 前端服务启动失败${NC}"
            echo "   查看日志: tail -50 /tmp/frontend.log"
        fi
    fi
else
    echo "   未找到 systemd 服务，手动启动..."
    cd "$FRONTEND_DIR"
    nohup npm start > /tmp/frontend.log 2>&1 &
    sleep 3
    if pgrep -f "next.*start" > /dev/null; then
        echo -e "${GREEN}✅ 前端服务已启动${NC}"
    else
        echo -e "${RED}❌ 前端服务启动失败${NC}"
        echo "   查看日志: tail -50 /tmp/frontend.log"
    fi
fi

echo ""
echo "============================================================"
echo "✅ 修复完成！"
echo "============================================================"
echo ""
echo "📝 检查步骤："
echo "   1. 检查端口: ss -tlnp | grep :3000"
echo "   2. 检查进程: ps aux | grep -E 'next|node.*3000'"
echo "   3. 测试访问: curl http://localhost:3000"
echo "   4. 查看日志: tail -f /tmp/frontend.log"
echo ""

