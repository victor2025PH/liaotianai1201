#!/bin/bash
# admin-backend 快速性能检查脚本
# 在服务器上直接运行此脚本

ADMIN_BACKEND_DIR="/home/ubuntu/telegram-ai-system/admin-backend"

echo "===== admin-backend 快速性能检查 ====="
echo ""

# 检查目录
if [ ! -d "$ADMIN_BACKEND_DIR" ]; then
    echo "❌ admin-backend 目录不存在: $ADMIN_BACKEND_DIR"
    exit 1
fi

cd "$ADMIN_BACKEND_DIR" || exit 1

echo "=== 1. PM2 进程状态 ==="
pm2 list | grep -E "admin|backend|uvicorn" || echo "未找到相关进程"
echo ""

echo "=== 2. 查看最近的错误日志 (PM2) ==="
echo "执行: pm2 logs --err --lines 50"
pm2 logs --err --lines 50 2>/dev/null | tail -20 || echo "无法获取 PM2 日志"
echo ""

echo "=== 3. 检查日志文件中的错误 ==="
if [ -d "logs" ]; then
    echo "最近的错误:"
    find logs -name "*.log" -type f -mtime -1 -exec tail -50 {} \; 2>/dev/null | grep -i "error\|exception\|traceback" | tail -10
else
    echo "⚠️  未找到 logs 目录"
fi
echo ""

echo "=== 4. 检查死循环模式 ==="
echo "查找重复错误:"
if [ -d "logs" ]; then
    find logs -name "*.log" -type f -mtime -1 -exec cat {} \; 2>/dev/null | grep -i "error" | sort | uniq -c | sort -rn | head -5
fi
echo ""

echo "=== 5. 检查同步路由 ==="
if [ -f "app/main.py" ]; then
    echo "同步路由 (可能阻塞):"
    grep -n "@app\.\(get\|post\|put\|delete\)" app/main.py | grep -B 5 -A 5 "def " | grep -v "async def" | head -10 || echo "未发现明显的同步路由"
else
    echo "❌ 未找到 app/main.py"
fi
echo ""

echo "=== 6. 检查数据库连接池配置 ==="
DB_FILES=$(find . -name "*.py" -exec grep -l "create_engine\|SessionLocal" {} \; 2>/dev/null | head -3)
if [ -n "$DB_FILES" ]; then
    for file in $DB_FILES; do
        echo "--- $file ---"
        echo "连接池配置:"
        grep -i "pool_size\|max_overflow\|pool_pre_ping\|pool_recycle" "$file" || echo "⚠️  未找到连接池配置"
        echo ""
    done
else
    echo "⚠️  未找到数据库配置文件"
fi
echo ""

echo "=== 7. 检查 Session 管理 ==="
if [ -n "$DB_FILES" ]; then
    for file in $DB_FILES; do
        echo "--- $file ---"
        echo "Session 使用:"
        grep -n "SessionLocal\|sessionmaker\|Depends.*Session\|with.*Session" "$file" | head -5
        echo ""
    done
fi
echo ""

echo "=== 8. 检查异步任务队列 ==="
if [ -f "celery_app.py" ] || [ -f "app/celery_app.py" ] || [ -f "tasks.py" ] || [ -f "app/tasks.py" ]; then
    echo "✓ 找到 Celery 配置"
    find . -name "*celery*.py" -o -name "tasks.py" 2>/dev/null | head -5
else
    echo "⚠️  未找到 Celery 配置"
fi
echo ""

echo "=== 9. 检查重计算任务 ==="
echo "查找可能的阻塞操作:"
find app -name "*.py" -exec grep -l "for.*in.*range\|while.*True" {} \; 2>/dev/null | head -5
echo ""

echo "=== 10. 当前资源使用 ==="
echo "CPU 和内存使用:"
ps aux | grep -E "uvicorn|gunicorn|python.*main" | grep -v grep | awk '{print $2, $3"%", $4"%", $11}' | head -5
echo ""

echo "===== 检查完成 ====="
echo ""
echo "下一步操作:"
echo "1. 查看详细日志: pm2 logs <app_name> --lines 200"
echo "2. 实时监控: pm2 monit"
echo "3. 运行完整分析: ./analyze_admin_backend.sh"
echo "4. 查看详细文档: cat ADMIN_BACKEND_PERFORMANCE_ANALYSIS.md"


