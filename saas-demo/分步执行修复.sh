#!/bin/bash
# 分步执行前端修复，每步都有清晰输出

cd ~/liaotian/saas-demo

echo "========================================"
echo "前端分步修复"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 步骤 1: 环境检查
echo "[步骤 1/8] 环境检查"
echo "目录: $(pwd)"
echo "Node: $(node -v 2>&1)"
echo "npm: $(npm -v 2>&1)"
echo ""

# 步骤 2: 检查 package.json
echo "[步骤 2/8] 检查 package.json"
if [ ! -f "package.json" ]; then
    echo "❌ package.json 不存在"
    exit 1
fi

# 检查端口配置
if grep -q '"dev": "next dev -p 3001"' package.json; then
    echo "⚠️  发现端口 3001，修复为 3000..."
    sed -i 's/"dev": "next dev -p 3001"/"dev": "next dev -p 3000"/g' package.json
    echo "✅ 已修复"
fi
echo "✅ package.json 正常"
echo ""

# 步骤 3: 停止旧进程
echo "[步骤 3/8] 停止旧进程"
pkill -f "next.*dev\|node.*3000\|node.*3001" || true
sleep 2
echo "✅ 完成"
echo ""

# 步骤 4: 检查依赖
echo "[步骤 4/8] 检查依赖"
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/next" ]; then
    echo "⚠️  依赖不完整，重新安装..."
    rm -rf node_modules package-lock.json
    npm install
    if [ $? -eq 0 ]; then
        echo "✅ 依赖安装成功"
    else
        echo "❌ 依赖安装失败"
        exit 1
    fi
else
    echo "✅ 依赖正常"
fi
echo ""

# 步骤 5: 检查构建
echo "[步骤 5/8] 检查构建"
if [ ! -d ".next" ]; then
    echo "⚠️  未构建，开始构建..."
    npm run build
    if [ $? -eq 0 ]; then
        echo "✅ 构建成功"
    else
        echo "❌ 构建失败，但继续尝试启动开发服务器"
    fi
else
    echo "✅ 构建存在"
fi
echo ""

# 步骤 6: 清理端口
echo "[步骤 6/8] 清理端口 3000"
if sudo lsof -i :3000 2>/dev/null | grep -q LISTEN; then
    sudo lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo "✅ 完成"
echo ""

# 步骤 7: 启动服务
echo "[步骤 7/8] 启动开发服务器"
npm run dev > /tmp/frontend_dev.log 2>&1 &
DEV_PID=$!
echo "进程 PID: $DEV_PID"
echo "等待 45 秒..."
sleep 45

# 检查进程
if ps -p $DEV_PID > /dev/null 2>&1; then
    echo "✅ 进程运行中"
else
    echo "❌ 进程已退出"
    echo "错误日志:"
    tail -30 /tmp/frontend_dev.log
    exit 1
fi
echo ""

# 步骤 8: 验证访问
echo "[步骤 8/8] 验证访问"
if curl -s --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 端口 3000 可以访问"
    echo ""
    echo "========================================"
    echo "✅ 修复成功！"
    echo "========================================"
    echo ""
    echo "前端服务已启动在: http://localhost:3000"
    echo "进程 PID: $DEV_PID"
    echo "日志: /tmp/frontend_dev.log"
    echo ""
    echo "查看日志: tail -f /tmp/frontend_dev.log"
    exit 0
else
    echo "❌ 端口 3000 无法访问"
    echo "查看日志:"
    tail -50 /tmp/frontend_dev.log
    exit 1
fi
