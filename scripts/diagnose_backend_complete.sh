#!/bin/bash
# 完整诊断后端问题
# 1. 检查 PM2 进程实际状态
# 2. 查看完整错误日志
# 3. 测试直接启动 uvicorn
# 4. 检查所有导入错误

set -e

echo "=========================================="
echo "🔍 完整诊断后端问题"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 1. 检查 PM2 进程状态
echo "1️⃣ 检查 PM2 进程状态"
echo "----------------------------------------"

pm2 list | grep -E "backend|luckyred-api" || echo "未找到后端进程"

echo ""

# 检查进程是否真的在运行
BACKEND_PID=$(pm2 jlist 2>/dev/null | grep -A 5 '"name":"backend"' | grep '"pid"' | grep -o '[0-9]*' | head -1 || echo "")

if [ -n "$BACKEND_PID" ]; then
    echo "后端进程 PID: $BACKEND_PID"
    
    # 检查进程是否真的存在
    if ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        echo "✅ 进程确实在运行"
        
        # 检查进程在做什么
        echo "进程状态:"
        ps -p "$BACKEND_PID" -o pid,stat,cmd | tail -1
    else
        echo "❌ 进程不存在（PM2 状态可能过时）"
    fi
else
    echo "⚠️  未找到后端进程 PID"
fi

echo ""

# 2. 检查端口监听
echo "2️⃣ 检查端口监听"
echo "----------------------------------------"

if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 端口 8000 正在监听"
    sudo lsof -i :8000
else
    echo "❌ 端口 8000 未监听"
    
    # 检查是否有进程尝试绑定但失败
    if [ -n "$BACKEND_PID" ]; then
        echo "检查进程的网络连接:"
        sudo netstat -tlnp 2>/dev/null | grep "$BACKEND_PID" || echo "进程没有网络连接"
    fi
fi

echo ""

# 3. 查看完整错误日志
echo "3️⃣ 查看完整错误日志"
echo "----------------------------------------"

echo "PM2 错误日志（最后 50 行）:"
echo "----------------------------------------"
pm2 logs backend --err --lines 50 --nostream 2>/dev/null | tail -50 || echo "无法获取错误日志"

echo ""
echo "PM2 输出日志（最后 50 行）:"
echo "----------------------------------------"
pm2 logs backend --out --lines 50 --nostream 2>/dev/null | tail -50 || echo "无法获取输出日志"

echo ""
echo "后端日志文件（如果存在）:"
echo "----------------------------------------"
if [ -f "$PROJECT_ROOT/logs/backend.log" ]; then
    tail -50 "$PROJECT_ROOT/logs/backend.log" || echo "无法读取日志文件"
else
    echo "日志文件不存在: $PROJECT_ROOT/logs/backend.log"
fi

echo ""

# 4. 测试直接启动 uvicorn（不通过 PM2）
echo "4️⃣ 测试直接启动 uvicorn"
echo "----------------------------------------"

cd "$PROJECT_ROOT/admin-backend" || exit 1

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在"
    exit 1
fi

source .venv/bin/activate

# 测试导入
echo "测试应用导入..."
if python3 -c "from app.main import app; print('✅ 应用导入成功')" 2>&1; then
    echo "✅ 应用可以正常导入"
else
    echo "❌ 应用导入失败"
    echo "错误信息:"
    python3 -c "from app.main import app" 2>&1 | head -30
    exit 1
fi

echo ""

# 尝试启动（后台运行，几秒后检查）
echo "尝试启动 uvicorn（测试 10 秒）..."
timeout 10 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 &
TEST_PID=$!

sleep 3

# 检查是否启动成功
if ps -p $TEST_PID > /dev/null 2>&1; then
    if sudo lsof -i :8000 >/dev/null 2>&1; then
        echo "✅ uvicorn 可以正常启动并监听端口"
        kill $TEST_PID 2>/dev/null || true
    else
        echo "⚠️  uvicorn 进程在运行，但端口未监听"
        kill $TEST_PID 2>/dev/null || true
    fi
else
    echo "❌ uvicorn 启动失败（进程立即退出）"
    wait $TEST_PID 2>/dev/null || true
fi

echo ""

# 5. 检查所有导入错误
echo "5️⃣ 检查所有导入错误"
echo "----------------------------------------"

echo "检查错误的导入（从 app.db 导入 get_db_session）:"
WRONG_IMPORTS=$(grep -r "from app.db import get_db_session" app/api/*.py 2>/dev/null | grep -v "deps.py" || echo "")

if [ -n "$WRONG_IMPORTS" ]; then
    echo "❌ 发现错误的导入:"
    echo "$WRONG_IMPORTS"
else
    echo "✅ 未发现错误的导入"
fi

echo ""

# 检查所有导入 get_db_session 的文件
echo "检查所有导入 get_db_session 的文件:"
ALL_IMPORTS=$(grep -r "get_db_session" app/api/*.py 2>/dev/null | grep "import" || echo "")

if [ -n "$ALL_IMPORTS" ]; then
    echo "所有导入 get_db_session 的位置:"
    echo "$ALL_IMPORTS" | while read -r line; do
        file=$(echo "$line" | cut -d: -f1)
        import_line=$(echo "$line" | cut -d: -f2-)
        if echo "$import_line" | grep -q "from app.db import get_db_session"; then
            echo "  ❌ $file: $import_line"
        elif echo "$import_line" | grep -q "from app.api.deps import get_db_session"; then
            echo "  ✅ $file: $import_line"
        else
            echo "  ⚠️  $file: $import_line"
        fi
    done
fi

echo ""

# 6. 检查应用启动时的错误
echo "6️⃣ 检查应用启动时的错误"
echo "----------------------------------------"

echo "测试应用初始化..."
python3 << 'PYTHON_EOF'
import sys
import traceback

try:
    print("导入 app.main...")
    from app.main import app
    print("✅ app.main 导入成功")
    
    print("检查 app 对象...")
    if app:
        print(f"✅ app 对象存在: {type(app)}")
        print(f"   路由数量: {len(app.routes)}")
    else:
        print("❌ app 对象为 None")
        
except Exception as e:
    print(f"❌ 导入失败: {e}")
    print("\n完整错误信息:")
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

if [ $? -ne 0 ]; then
    echo "❌ 应用初始化失败"
else
    echo "✅ 应用初始化成功"
fi

echo ""

# 7. 检查数据库连接
echo "7️⃣ 检查数据库连接"
echo "----------------------------------------"

python3 << 'PYTHON_EOF'
import sys
from app.db import SessionLocal, engine

try:
    print("测试数据库连接...")
    db = SessionLocal()
    db.execute("SELECT 1")
    db.close()
    print("✅ 数据库连接正常")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    sys.exit(1)
PYTHON_EOF

echo ""

# 8. 总结
echo "=========================================="
echo "📋 诊断总结"
echo "=========================================="
echo ""

cd "$PROJECT_ROOT" || exit 1

echo "如果发现问题，请执行以下步骤修复:"
echo ""
echo "1. 如果导入错误:"
echo "   修复所有 'from app.db import get_db_session' 为 'from app.api.deps import get_db_session'"
echo ""
echo "2. 如果应用无法启动:"
echo "   查看完整错误日志: pm2 logs backend --lines 100"
echo ""
echo "3. 如果端口未监听:"
echo "   检查进程是否真的在运行: ps aux | grep uvicorn"
echo ""
echo "4. 如果数据库连接失败:"
echo "   检查数据库配置和文件权限"
echo ""

