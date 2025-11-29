#!/bin/bash
# 前端自愈诊断和修复脚本

set -e

cd ~/liaotian/saas-demo

echo "========================================"
echo "前端自愈诊断和修复"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

LOG_FILE="/tmp/frontend_auto_fix_$(date +%s).log"
exec > >(tee -a "$LOG_FILE")
exec 2>&1

# 1. 环境信息
echo "[1] 环境信息"
echo "目录: $(pwd)"
echo "Node: $(node -v 2>&1)"
echo "npm: $(npm -v 2>&1)"
echo ""

# 检查是否是 Next.js 项目
if [ ! -f "package.json" ]; then
    echo "❌ 错误: 找不到 package.json"
    exit 1
fi

if ! grep -q '"next"' package.json; then
    echo "❌ 错误: 这不是一个 Next.js 项目"
    exit 1
fi

echo "✅ 确认为 Next.js 项目"
echo ""

# 2. 读取现有错误日志
echo "[2] 读取现有错误日志"
if [ -f "/tmp/frontend_detailed.log" ]; then
    echo "发现日志: /tmp/frontend_detailed.log"
    tail -50 /tmp/frontend_detailed.log | head -30
fi
echo ""

# 3. 停止旧进程
echo "[3] 停止旧进程"
pkill -f "next.*dev\|node.*3000" || true
sleep 2

# 清理端口
if sudo lsof -i :3000 2>/dev/null | grep -q LISTEN; then
    echo "清理端口 3000..."
    sudo lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo ""

# 4. 尝试运行并捕获错误
echo "[4] 尝试运行 npm run dev (30秒超时)"
timeout 30 npm run dev 2>&1 | head -100 || ERROR_CODE=$?

if [ -n "$ERROR_CODE" ]; then
    echo "❌ npm run dev 失败，错误码: $ERROR_CODE"
    echo "分析错误信息..."
fi
echo ""

# 5. 检查依赖
echo "[5] 检查依赖"
if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules 不存在，安装依赖..."
    rm -rf package-lock.json
    npm install
elif [ ! -f "node_modules/.bin/next" ]; then
    echo "⚠️  Next.js 未正确安装，重新安装依赖..."
    rm -rf node_modules package-lock.json
    npm install
else
    echo "✅ 依赖存在"
fi
echo ""

# 6. 检查构建
echo "[6] 检查构建"
if [ ! -d ".next" ]; then
    echo "⚠️  .next 不存在，尝试构建..."
    npm run build 2>&1 | tail -50
else
    echo "✅ .next 存在"
fi
echo ""

# 7. 再次尝试启动
echo "[7] 再次尝试启动"
pkill -f "next.*dev\|node.*3000" || true
sleep 2

echo "启动服务并等待 30 秒..."
npm run dev > /tmp/frontend_start.log 2>&1 &
DEV_PID=$!
echo "进程 PID: $DEV_PID"
sleep 30

# 检查进程
if ps -p $DEV_PID > /dev/null 2>&1; then
    echo "✅ 进程仍在运行"
else
    echo "❌ 进程已退出"
    echo "查看日志:"
    tail -50 /tmp/frontend_start.log
fi

# 检查端口
if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 端口 3000 可以访问"
else
    echo "❌ 端口 3000 无法访问"
    echo "查看启动日志:"
    tail -50 /tmp/frontend_start.log
fi

echo ""
echo "========================================"
echo "诊断完成"
echo "========================================"
echo "完整日志: $LOG_FILE"
echo "启动日志: /tmp/frontend_start.log"
