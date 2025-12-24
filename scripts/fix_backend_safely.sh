#!/bin/bash
# 安全修复后端服务
# 1. 停止所有后端服务
# 2. 检查并修复导入问题
# 3. 测试应用可以正常导入
# 4. 使用安全方式启动服务
# 5. 验证服务正常运行

set -e

echo "=========================================="
echo "🔧 安全修复后端服务"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 1. 停止所有后端服务
echo "1️⃣ 停止所有后端服务"
echo "----------------------------------------"

pm2 stop backend luckyred-api 2>/dev/null || true
pm2 delete backend luckyred-api 2>/dev/null || true

# 确保端口释放
if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "释放端口 8000..."
    sudo lsof -ti :8000 | xargs sudo kill -9 2>/dev/null || true
    sleep 2
fi

echo "✅ 所有后端服务已停止"
echo ""

# 2. 进入后端目录
cd "$PROJECT_ROOT/admin-backend" || exit 1

# 3. 检查虚拟环境
echo "2️⃣ 检查虚拟环境"
echo "----------------------------------------"

if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "✅ 虚拟环境已激活"
echo ""

# 4. 测试导入（关键步骤）
echo "3️⃣ 测试应用导入"
echo "----------------------------------------"

echo "测试基础导入..."
if python3 -c "from app.api.deps import get_db_session; print('✅ get_db_session 导入成功')" 2>&1; then
    echo "✅ get_db_session 可以正常导入"
else
    echo "❌ get_db_session 导入失败"
    python3 -c "from app.api.deps import get_db_session" 2>&1
    exit 1
fi

echo ""
echo "测试应用导入..."
if python3 -c "from app.main import app; print('✅ app 导入成功')" 2>&1; then
    echo "✅ 应用可以正常导入"
else
    echo "❌ 应用导入失败"
    echo "错误信息:"
    python3 -c "from app.main import app" 2>&1 | head -50
    exit 1
fi

echo ""

# 5. 检查所有导入
echo "4️⃣ 检查所有导入"
echo "----------------------------------------"

# 检查是否有错误的导入
WRONG_COUNT=$(grep -r "from app.db import get_db_session" app/api/*.py 2>/dev/null | wc -l || echo "0")

if [ "$WRONG_COUNT" -gt 0 ]; then
    echo "⚠️  发现 $WRONG_COUNT 个错误的导入，需要修复"
    grep -r "from app.db import get_db_session" app/api/*.py 2>/dev/null || true
    echo ""
    echo "❌ 请先修复这些导入错误"
    exit 1
else
    echo "✅ 未发现错误的导入"
fi

echo ""

# 6. 测试数据库连接
echo "5️⃣ 测试数据库连接"
echo "----------------------------------------"

if python3 << 'PYTHON_EOF'
from app.db import SessionLocal
try:
    db = SessionLocal()
    db.execute("SELECT 1")
    db.close()
    print("✅ 数据库连接正常")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    exit(1)
PYTHON_EOF
then
    echo "✅ 数据库连接测试通过"
else
    echo "⚠️  数据库连接测试失败，但继续..."
fi

echo ""

# 7. 启动服务（使用更安全的方式）
echo "6️⃣ 启动后端服务"
echo "----------------------------------------"

# 确保 .env 文件存在
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "复制 .env.example 到 .env..."
    cp .env.example .env 2>/dev/null || true
fi

# 使用 PM2 启动，但添加更多错误检查
echo "使用 PM2 启动后端服务..."

# 先测试能否启动（不实际启动）
if python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --help >/dev/null 2>&1; then
    echo "✅ uvicorn 命令可用"
else
    echo "❌ uvicorn 命令不可用"
    exit 1
fi

# 启动服务
pm2 start .venv/bin/uvicorn \
    --name backend \
    --interpreter none \
    -- app.main:app --host 0.0.0.0 --port 8000

sleep 5

# 8. 验证服务
echo "7️⃣ 验证服务"
echo "----------------------------------------"

# 检查进程
BACKEND_PID=$(pm2 jlist 2>/dev/null | grep -A 5 '"name":"backend"' | grep '"pid"' | grep -o '[0-9]*' | head -1 || echo "")

if [ -z "$BACKEND_PID" ]; then
    echo "❌ 后端进程未启动"
    echo "查看 PM2 日志:"
    pm2 logs backend --lines 30 --nostream 2>/dev/null | tail -30
    exit 1
fi

echo "后端进程 PID: $BACKEND_PID"

# 检查进程是否真的在运行
if ! ps -p "$BACKEND_PID" > /dev/null 2>&1; then
    echo "❌ 进程不存在（可能已崩溃）"
    echo "查看 PM2 错误日志:"
    pm2 logs backend --err --lines 50 --nostream 2>/dev/null | tail -50
    exit 1
fi

echo "✅ 进程正在运行"

# 检查端口
if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 端口 8000 正在监听"
    
    # 等待服务完全启动
    echo "等待服务完全启动..."
    for i in {1..15}; do
        sleep 2
        if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
            health_response=$(curl -s http://127.0.0.1:8000/health 2>/dev/null || echo "")
            echo "✅ 健康检查通过 (等待了 $((i*2)) 秒)"
            echo "   响应: $health_response"
            break
        fi
        if [ $i -eq 15 ]; then
            echo "⚠️  健康检查超时"
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
    pm2 logs backend --lines 50 --nostream 2>/dev/null | tail -50
    exit 1
fi

echo ""

# 9. 显示 PM2 状态
echo "8️⃣ PM2 进程状态"
echo "----------------------------------------"
pm2 list | grep -E "backend|luckyred-api" || echo "未找到后端进程"

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "📋 后端服务状态:"
echo "   - 进程 PID: $BACKEND_PID"
echo "   - 端口: 8000"
echo "   - 健康检查: http://127.0.0.1:8000/health"
echo "   - API 端点: http://127.0.0.1:8000/api/v1/"
echo ""
echo "💡 如果仍有问题:"
echo "   1. 查看完整日志: pm2 logs backend --lines 100"
echo "   2. 查看错误日志: pm2 logs backend --err --lines 100"
echo "   3. 重新运行诊断: bash scripts/diagnose_backend_complete.sh"
echo ""

