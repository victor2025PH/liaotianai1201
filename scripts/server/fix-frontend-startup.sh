#!/bin/bash
# ============================================================
# 修复前端服务启动问题
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "=========================================="
echo "🔧 修复前端服务启动问题"
echo "=========================================="
echo ""

# 1. 检查前端目录
echo "[1/6] 检查前端目录..."
echo "----------------------------------------"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ 前端目录不存在: $FRONTEND_DIR"
    exit 1
fi

cd "$FRONTEND_DIR" || exit 1
echo "✅ 前端目录: $FRONTEND_DIR"
echo "当前目录: $(pwd)"
echo ""

# 2. 停止现有的前端进程
echo "[2/6] 停止现有的前端进程..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    pm2 stop next-server 2>/dev/null || true
    pm2 stop frontend 2>/dev/null || true
    pm2 delete next-server 2>/dev/null || true
    pm2 delete frontend 2>/dev/null || true
    echo "✅ 已停止现有前端进程"
else
    echo "⚠️  PM2 未安装"
fi

# 杀死可能占用端口 3000 的进程
PORT_3000_PID=$(sudo lsof -ti:3000 2>/dev/null || echo "")
if [ -n "$PORT_3000_PID" ]; then
    echo "发现端口 3000 被占用，PID: $PORT_3000_PID"
    sudo kill -9 $PORT_3000_PID 2>/dev/null || true
    sleep 1
fi
echo ""

# 3. 检查 Node.js 和 npm
echo "[3/6] 检查 Node.js 和 npm..."
echo "----------------------------------------"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js 版本: $NODE_VERSION"
else
    echo "❌ Node.js 未安装"
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm 版本: $NPM_VERSION"
else
    echo "❌ npm 未安装"
    exit 1
fi
echo ""

# 4. 检查依赖和构建文件
echo "[4/6] 检查依赖和构建文件..."
echo "----------------------------------------"
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules 不存在，安装依赖..."
    npm install
else
    echo "✅ node_modules 存在"
fi

if [ ! -d ".next" ]; then
    echo "⚠️  .next 目录不存在，需要构建..."
    echo "开始构建（这可能需要几分钟）..."
    npm run build
    if [ $? -ne 0 ]; then
        echo "❌ 构建失败"
        echo "查看构建错误："
        npm run build 2>&1 | tail -20
        exit 1
    fi
    echo "✅ 构建完成"
else
    echo "✅ .next 目录存在"
fi
echo ""

# 5. 检查 package.json 和启动脚本
echo "[5/6] 检查 package.json..."
echo "----------------------------------------"
if [ -f "package.json" ]; then
    echo "✅ package.json 存在"
    if grep -q '"start"' package.json; then
        START_SCRIPT=$(grep -A 1 '"start"' package.json | grep -o '".*"' | head -1 | tr -d '"')
        echo "启动脚本: $START_SCRIPT"
    else
        echo "⚠️  package.json 中缺少 start 脚本"
    fi
else
    echo "❌ package.json 不存在"
    exit 1
fi
echo ""

# 6. 启动前端服务
echo "[6/6] 启动前端服务..."
echo "----------------------------------------"

# 尝试使用 PM2 启动
if command -v pm2 &> /dev/null; then
    echo "使用 PM2 启动前端服务..."
    
    # 先尝试直接启动 npm
    pm2 start npm --name next-server -- start
    
    sleep 5
    
    # 检查状态
    pm2 list | grep next-server
    
    # 检查日志
    echo ""
    echo "查看启动日志（最近 20 行）..."
    pm2 logs next-server --lines 20 --nostream 2>/dev/null || echo "无法获取日志"
    
    # 检查端口
    sleep 3
    if sudo ss -tlnp | grep -q ":3000 "; then
        echo ""
        echo "✅ 前端服务已启动，端口 3000 正在监听"
    else
        echo ""
        echo "⚠️  端口 3000 未监听，检查错误..."
        pm2 logs next-server --lines 50 --nostream 2>/dev/null | tail -30
    fi
else
    echo "⚠️  PM2 未安装，尝试直接启动..."
    npm start &
    sleep 5
    
    if sudo ss -tlnp | grep -q ":3000 "; then
        echo "✅ 前端服务已启动"
    else
        echo "❌ 前端服务启动失败"
    fi
fi
echo ""

# 7. 测试连接
echo "测试前端服务连接..."
echo "----------------------------------------"
sleep 2

if curl -s http://127.0.0.1:3000 > /dev/null; then
    echo "✅ 前端服务可以响应"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000)
    echo "   HTTP 状态码: $HTTP_CODE"
else
    echo "❌ 前端服务无法响应"
    echo "   检查 PM2 日志: pm2 logs next-server"
fi
echo ""

# 8. 检查 Nginx 配置
echo "检查 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置正确"
    echo "重新加载 Nginx..."
    sudo systemctl reload nginx
    sleep 2
    
    # 测试 HTTPS
    if curl -s -k https://127.0.0.1 > /dev/null; then
        echo "✅ HTTPS 本地连接正常"
    else
        echo "⚠️  HTTPS 本地连接异常"
    fi
else
    echo "❌ Nginx 配置有错误"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果前端服务仍然无法启动，请："
echo "  1. 查看详细日志: pm2 logs next-server"
echo "  2. 检查构建文件: ls -la .next/"
echo "  3. 重新构建: npm run build"
echo "  4. 检查端口占用: sudo lsof -i:3000"
echo ""

