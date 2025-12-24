#!/bin/bash
# 根据错误类型自动修复后端问题
# 这个脚本会根据常见错误自动修复

set -e

echo "=========================================="
echo "🔧 自动修复后端常见错误"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT/admin-backend" || exit 1

source .venv/bin/activate

# 修复 1: SQLAlchemy text() 问题
echo "修复 1: SQLAlchemy text() 语法问题"
echo "----------------------------------------"

# 检查诊断脚本中的数据库测试
if grep -q 'db.execute("SELECT 1")' "$PROJECT_ROOT/scripts/diagnose_backend_complete.sh" 2>/dev/null; then
    echo "修复诊断脚本中的数据库测试..."
    sed -i 's/db.execute("SELECT 1")/db.execute(text("SELECT 1"))/g' "$PROJECT_ROOT/scripts/diagnose_backend_complete.sh"
    # 确保导入 text
    if ! grep -q "from sqlalchemy import text" "$PROJECT_ROOT/scripts/diagnose_backend_complete.sh"; then
        sed -i '/from app.db import SessionLocal/a from sqlalchemy import text' "$PROJECT_ROOT/scripts/diagnose_backend_complete.sh"
    fi
    echo "✅ 已修复诊断脚本"
fi

# 修复 2: 检查并安装缺失的依赖
echo ""
echo "修复 2: 检查依赖"
echo "----------------------------------------"

if ! python3 -c "import psutil" 2>/dev/null; then
    echo "安装 psutil..."
    pip install psutil 2>&1 | tail -5
fi

if ! python3 -c "import prometheus_client" 2>/dev/null; then
    echo "安装 prometheus_client..."
    pip install prometheus-client 2>&1 | tail -5
fi

echo "✅ 依赖检查完成"
echo ""

# 修复 3: 检查数据库文件
echo "修复 3: 检查数据库文件"
echo "----------------------------------------"

DB_FILE="$PROJECT_ROOT/admin-backend/admin.db"
if [ -f "$DB_FILE" ]; then
    echo "✅ 数据库文件存在: $DB_FILE"
    echo "   文件大小: $(du -sh "$DB_FILE" | cut -f1)"
    echo "   文件权限: $(ls -l "$DB_FILE" | awk '{print $1, $3, $4}')"
    
    # 检查文件权限
    if [ ! -r "$DB_FILE" ] || [ ! -w "$DB_FILE" ]; then
        echo "⚠️  数据库文件权限可能有问题，尝试修复..."
        sudo chmod 664 "$DB_FILE" 2>/dev/null || true
        sudo chown ubuntu:ubuntu "$DB_FILE" 2>/dev/null || true
    fi
else
    echo "⚠️  数据库文件不存在，将在首次启动时创建"
fi

echo ""

# 修复 4: 检查 .env 文件
echo "修复 4: 检查环境变量配置"
echo "----------------------------------------"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "复制 .env.example 到 .env..."
        cp .env.example .env
        echo "✅ 已创建 .env 文件"
    else
        echo "⚠️  .env 文件不存在，但这不是致命错误"
    fi
else
    echo "✅ .env 文件存在"
fi

echo ""

# 修复 5: 测试数据库连接（使用正确的语法）
echo "修复 5: 测试数据库连接"
echo "----------------------------------------"

python3 << 'PYTHON_EOF'
from sqlalchemy import text
from app.db import SessionLocal

try:
    print("测试数据库连接...")
    db = SessionLocal()
    # 使用 text() 函数
    result = db.execute(text("SELECT 1"))
    db.close()
    print("✅ 数据库连接正常")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo "✅ 数据库连接测试通过"
else
    echo "❌ 数据库连接测试失败"
    exit 1
fi

echo ""

# 修复 6: 检查所有导入
echo "修复 6: 检查所有导入"
echo "----------------------------------------"

echo "测试关键导入..."
python3 << 'PYTHON_EOF'
import sys

errors = []

# 测试基础导入
try:
    from app.api.deps import get_db_session
    print("✅ get_db_session 导入成功")
except Exception as e:
    print(f"❌ get_db_session 导入失败: {e}")
    errors.append(f"get_db_session: {e}")

# 测试应用导入
try:
    from app.main import app
    print("✅ app 导入成功")
except Exception as e:
    print(f"❌ app 导入失败: {e}")
    errors.append(f"app: {e}")
    import traceback
    traceback.print_exc()

if errors:
    print(f"\n❌ 发现 {len(errors)} 个导入错误")
    sys.exit(1)
else:
    print("\n✅ 所有导入测试通过")
PYTHON_EOF

if [ $? -ne 0 ]; then
    echo "❌ 导入测试失败，请检查错误信息"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "现在可以尝试手动启动后端:"
echo "  cd $PROJECT_ROOT/admin-backend"
echo "  source .venv/bin/activate"
echo "  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""

