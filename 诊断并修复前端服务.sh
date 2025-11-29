#!/bin/bash
# 诊断并修复前端服务问题

set -e

cd ~/liaotian/saas-demo

echo "========================================"
echo "诊断并修复前端服务"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 1. 检查环境
echo "[1/6] 检查环境..."
echo "当前目录: $(pwd)"
if [ ! -f "package.json" ]; then
    echo "❌ 错误: 找不到 package.json"
    exit 1
fi
echo "✅ package.json 存在"
echo ""

# 2. 检查 Node.js 和 npm
echo "[2/6] 检查 Node.js 和 npm..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi
echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"
echo ""

# 3. 检查依赖
echo "[3/6] 检查依赖..."
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules 不存在，安装依赖..."
    npm install
else
    echo "✅ node_modules 存在"
fi
echo ""

# 4. 停止现有进程
echo "[4/6] 停止现有进程..."
pkill -f "next.*dev\|node.*3000" || true
sleep 3

# 检查端口是否被占用
if sudo lsof -i :3000 2>/dev/null | grep -q LISTEN; then
    echo "⚠️  端口 3000 被占用，正在清理..."
    sudo lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo "✅ 端口已清理"
echo ""

# 5. 检查是否需要构建
echo "[5/6] 检查构建..."
if [ ! -d ".next" ]; then
    echo "⚠️  .next 目录不存在，开始构建..."
    npm run build
    echo "✅ 构建完成"
else
    echo "✅ .next 目录存在"
fi
echo ""

# 6. 启动前端服务
echo "[6/6] 启动前端服务..."
LOG_FILE="/tmp/frontend_$(date +%s).log"
echo "日志文件: $LOG_FILE"

# 使用 screen 启动以便查看输出
if command -v screen &> /dev/null; then
    screen -dmS frontend bash -c "cd ~/liaotian/saas-demo && npm run dev > $LOG_FILE 2>&1"
    echo "✅ 前端服务已在 screen 会话中启动"
    echo "查看会话: screen -r frontend"
else
    # 使用 nohup
    nohup npm run dev > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "✅ 前端服务已启动 (PID: $PID)"
fi

echo ""
echo "等待前端启动（30秒）..."
sleep 30

# 验证启动
echo ""
echo "========================================"
echo "验证结果"
echo "========================================"

# 检查进程
if ps aux | grep -E "next.*dev|node.*3000" | grep -v grep; then
    echo "✅ 前端进程正在运行"
else
    echo "❌ 前端进程未运行"
    echo "查看日志: tail -50 $LOG_FILE"
fi

# 检查端口
if sudo netstat -tlnp | grep -q ":3000"; then
    echo "✅ 端口 3000 正在监听"
else
    echo "❌ 端口 3000 未监听"
fi

# 检查 HTTP 响应
if curl -s --max-time 5 http://localhost:3000 | head -1 | grep -q "html\|DOCTYPE"; then
    echo "✅ 前端服务可以访问"
else
    echo "❌ 前端服务无法访问"
    echo "查看日志: tail -50 $LOG_FILE"
fi

echo ""
echo "日志文件: $LOG_FILE"
echo "查看日志: tail -f $LOG_FILE"
