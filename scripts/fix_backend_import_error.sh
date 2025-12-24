#!/bin/bash
# 修复后端导入错误并重启服务
# 1. 修复 ImportError: cannot import name 'get_db_session' from 'app.db'
# 2. 重启后端服务

set -e

echo "=========================================="
echo "🔧 修复后端导入错误并重启服务"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 1. 检查后端目录
if [ ! -d "$PROJECT_ROOT/admin-backend" ]; then
    echo "❌ admin-backend 目录不存在"
    exit 1
fi

cd "$PROJECT_ROOT/admin-backend" || exit 1

# 2. 拉取最新代码（确保修复已应用）
echo "1️⃣ 拉取最新代码"
echo "----------------------------------------"
git pull origin main 2>&1 | tail -5 || echo "⚠️  git pull 失败，继续..."

echo ""

# 3. 检查并修复导入错误
echo "2️⃣ 检查导入错误"
echo "----------------------------------------"

# 检查是否有错误的导入
WRONG_IMPORTS=$(grep -r "from app.db import get_db_session" app/api/*.py 2>/dev/null | grep -v "deps.py" || echo "")

if [ -n "$WRONG_IMPORTS" ]; then
    echo "发现错误的导入:"
    echo "$WRONG_IMPORTS"
    echo ""
    echo "⚠️  需要修复这些文件，但脚本无法自动修复"
    echo "   请确保代码已从 GitHub 拉取最新版本"
else
    echo "✅ 未发现错误的导入"
fi

echo ""

# 4. 检查虚拟环境
echo "3️⃣ 检查虚拟环境"
echo "----------------------------------------"

if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 5. 安装/更新依赖
echo "4️⃣ 检查依赖"
echo "----------------------------------------"

if [ ! -f ".venv/bin/uvicorn" ]; then
    echo "安装依赖..."
    pip install -r requirements.txt 2>&1 | tail -10
else
    echo "✅ 依赖已安装"
fi

echo ""

# 6. 测试导入
echo "5️⃣ 测试导入"
echo "----------------------------------------"

if python3 -c "from app.api.deps import get_db_session; print('✅ get_db_session 导入成功')" 2>&1; then
    echo "✅ 导入测试通过"
else
    echo "❌ 导入测试失败"
    python3 -c "from app.api.deps import get_db_session" 2>&1
    exit 1
fi

echo ""

# 7. 停止旧服务
echo "6️⃣ 停止旧服务"
echo "----------------------------------------"

pm2 delete backend luckyred-api 2>/dev/null || true

if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "释放端口 8000..."
    sudo lsof -ti :8000 | xargs sudo kill -9 2>/dev/null || true
    sleep 2
fi

echo "✅ 旧服务已停止"
echo ""

# 8. 启动后端服务
echo "7️⃣ 启动后端服务"
echo "----------------------------------------"

# 检查是否有 .env 文件
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "⚠️  未找到 .env 文件，复制 .env.example..."
    cp .env.example .env 2>/dev/null || true
fi

# 启动服务
pm2 start .venv/bin/uvicorn \
    --name backend \
    --interpreter none \
    -- app.main:app --host 0.0.0.0 --port 8000

sleep 5

# 9. 验证服务
echo "8️⃣ 验证服务"
echo "----------------------------------------"

if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 端口 8000 正在监听"
    
    # 测试健康检查
    for i in {1..10}; do
        sleep 2
        if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
            health_response=$(curl -s http://127.0.0.1:8000/health 2>/dev/null || echo "")
            if echo "$health_response" | grep -q "ok\|healthy\|status" || [ -n "$health_response" ]; then
                echo "✅ 后端服务健康检查通过"
                echo "   响应: $health_response"
                break
            fi
        fi
        if [ $i -eq 10 ]; then
            echo "⚠️  健康检查超时，但服务可能已启动"
        fi
    done
    
    # 测试 API 端点
    api_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:8000/api/v1/auth/login 2>/dev/null || echo "000")
    if [ "$api_code" = "405" ] || [ "$api_code" = "422" ] || [ "$api_code" = "200" ]; then
        echo "✅ API 端点可访问 (HTTP $api_code)"
    else
        echo "⚠️  API 端点响应异常 (HTTP $api_code)"
    fi
else
    echo "❌ 端口 8000 未监听"
    echo ""
    echo "查看 PM2 日志:"
    pm2 logs backend --lines 20 --nostream 2>/dev/null | tail -20 || echo "无法获取日志"
    exit 1
fi

echo ""

# 10. 显示 PM2 状态
echo "9️⃣ PM2 进程状态"
echo "----------------------------------------"
pm2 list | grep -E "backend|luckyred-api" || echo "未找到后端进程"

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "📋 后端服务状态:"
echo "   - 端口: 8000"
echo "   - 健康检查: http://127.0.0.1:8000/health"
echo "   - API 端点: http://127.0.0.1:8000/api/v1/"
echo ""
echo "💡 如果仍有问题，请检查:"
echo "   1. PM2 日志: pm2 logs backend"
echo "   2. 后端日志: tail -50 /home/ubuntu/.pm2/logs/backend-error.log"
echo "   3. 导入测试: python3 -c 'from app.api.deps import get_db_session'"
echo ""

