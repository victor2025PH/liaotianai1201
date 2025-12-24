#!/bin/bash
# 手动调试后端 - 精准排查 502 问题
# 1. 停止 PM2 干扰
# 2. 清理端口占用
# 3. 手动启动后端查看实时错误
# 4. 根据错误提供修复方案

set -e

echo "=========================================="
echo "🔍 手动调试后端 - 精准排查"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 第一步：停止 PM2 的干扰
echo "第一步：停止 PM2 的干扰"
echo "----------------------------------------"

echo "停止所有 PM2 进程..."
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true

echo "✅ PM2 进程已停止"
echo ""

# 检查并清理端口 8000
echo "检查端口 8000 占用情况..."
if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "⚠️  发现端口 8000 被占用:"
    sudo lsof -i :8000
    
    echo ""
    echo "清理端口 8000..."
    sudo lsof -ti :8000 | xargs sudo kill -9 2>/dev/null || true
    sleep 2
    
    if sudo lsof -i :8000 >/dev/null 2>&1; then
        echo "❌ 端口清理失败，仍有进程占用"
        sudo lsof -i :8000
        exit 1
    else
        echo "✅ 端口 8000 已释放"
    fi
else
    echo "✅ 端口 8000 未被占用"
fi

echo ""

# 第二步：进入后端目录
echo "第二步：准备手动启动后端"
echo "----------------------------------------"

cd "$PROJECT_ROOT/admin-backend" || {
    echo "❌ 无法进入 admin-backend 目录"
    exit 1
}

echo "当前目录: $(pwd)"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在"
    exit 1
fi

source .venv/bin/activate

echo "✅ 虚拟环境已激活"
echo "Python 路径: $(which python3)"
echo ""

# 检查关键文件
if [ ! -f "app/main.py" ]; then
    echo "❌ app/main.py 不存在"
    exit 1
fi

echo "✅ 关键文件存在"
echo ""

# 第三步：测试导入（不启动服务）
echo "第三步：测试应用导入"
echo "----------------------------------------"

echo "测试导入 app.main..."
if python3 -c "from app.main import app; print('✅ 导入成功')" 2>&1; then
    echo "✅ 应用可以正常导入"
else
    echo "❌ 应用导入失败"
    echo ""
    echo "错误信息:"
    python3 -c "from app.main import app" 2>&1 | head -50
    exit 1
fi

echo ""

# 第四步：手动启动后端（关键步骤）
echo "第四步：手动启动后端（查看实时错误）"
echo "----------------------------------------"
echo ""
echo "⚠️  现在将手动启动后端，请观察输出..."
echo "   如果看到错误，请记录完整的错误信息"
echo "   按 Ctrl+C 可以停止"
echo ""
echo "----------------------------------------"
echo ""

# 使用 timeout 限制运行时间，避免无限运行
# 但实际运行时，用户应该手动停止
echo "启动命令: python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "开始启动..."
echo ""

# 直接启动，让用户看到实时输出
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

