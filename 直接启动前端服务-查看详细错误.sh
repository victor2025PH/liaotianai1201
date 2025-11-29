#!/bin/bash
# 直接启动前端服务并查看详细错误

cd ~/liaotian/saas-demo

echo "========================================"
echo "直接启动前端服务"
echo "========================================"
echo ""

# 停止现有进程
echo "1. 停止现有进程..."
pkill -f "next.*dev\|node.*3000" || true
sleep 2
echo "完成"
echo ""

# 检查目录
echo "2. 检查目录..."
echo "当前目录: $(pwd)"
if [ ! -f "package.json" ]; then
    echo "❌ 错误: 找不到 package.json"
    exit 1
fi
echo "✅ package.json 存在"
echo ""

# 检查依赖
echo "3. 检查依赖..."
if [ ! -d "node_modules" ]; then
    echo "⚠️  依赖未安装，正在安装..."
    npm install
else
    echo "✅ 依赖已安装"
fi
echo ""

# 检查端口
echo "4. 检查端口 3000..."
if sudo lsof -i :3000 2>/dev/null | grep -q LISTEN; then
    echo "⚠️  端口被占用，清理中..."
    sudo lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo "✅ 端口已清理"
echo ""

# 启动服务（在前台运行以便看到错误）
echo "5. 启动前端服务..."
echo "========================================"
echo "前端服务正在启动..."
echo "按 Ctrl+C 停止"
echo "========================================"
echo ""

# 直接运行，显示所有输出
npm run dev
