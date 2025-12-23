#!/bin/bash
# 修复 Alembic 迁移错误 - 处理已存在的表

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"

echo "🔧 修复 Alembic 迁移错误..."

cd "$BACKEND_DIR" || {
    echo "❌ 无法进入后端目录"
    exit 1
}

# 1. 检查虚拟环境
if [ -d ".venv" ]; then
    echo "✅ 找到虚拟环境 .venv"
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "✅ 找到虚拟环境 venv"
    source venv/bin/activate
else
    echo "⚠️  未找到虚拟环境，使用系统 Python"
fi

# 2. 检查数据库文件
DB_FILE="admin.db"
if [ -f "$DB_FILE" ]; then
    echo "📊 数据库文件存在: $DB_FILE"
    
    # 检查表是否已存在
    echo "🔍 检查现有表..."
    python3 << EOF
import sqlite3
import sys

try:
    conn = sqlite3.connect('$DB_FILE')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"现有表: {', '.join(tables) if tables else '无'}")
    
    if 'users' in tables:
        print("⚠️  users 表已存在")
        sys.exit(1)
    else:
        print("✅ users 表不存在，可以继续迁移")
        sys.exit(0)
except Exception as e:
    print(f"❌ 检查失败: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 1 ]; then
        echo "⚠️  检测到 users 表已存在"
        echo "💡 选项 1: 标记迁移为已执行（推荐）"
        echo "💡 选项 2: 删除数据库重新迁移（会丢失数据）"
        read -p "选择操作 [1/2]: " choice
        
        if [ "$choice" = "2" ]; then
            echo "🗑️  备份并删除数据库..."
            cp "$DB_FILE" "${DB_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
            rm -f "$DB_FILE"
            echo "✅ 数据库已删除，可以重新迁移"
        else
            echo "📝 标记迁移为已执行..."
            # 获取当前迁移版本
            CURRENT_REV=$(alembic current 2>/dev/null | grep -oP '^\w+' || echo "")
            
            if [ -z "$CURRENT_REV" ]; then
                # 标记初始迁移为已执行
                INITIAL_REV=$(alembic history | grep "000_initial_base" | head -1 | awk '{print $1}')
                if [ -n "$INITIAL_REV" ]; then
                    echo "标记 $INITIAL_REV 为已执行..."
                    alembic stamp "$INITIAL_REV" || {
                        echo "⚠️  标记失败，尝试其他方法"
                    }
                fi
            else
                echo "当前版本: $CURRENT_REV"
            fi
        fi
    fi
else
    echo "📊 数据库文件不存在，将创建新数据库"
fi

# 3. 运行迁移
echo "🔄 运行数据库迁移..."
alembic upgrade head || {
    echo "❌ 迁移失败"
    echo "💡 如果是因为表已存在，可以尝试："
    echo "   1. alembic stamp head  # 标记所有迁移为已执行"
    echo "   2. 或手动修复迁移脚本"
    exit 1
}

echo "✅ 迁移完成！"

