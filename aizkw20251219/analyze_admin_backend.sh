#!/bin/bash
# admin-backend 性能分析脚本
# 在服务器上执行此脚本来分析性能问题

ADMIN_BACKEND_DIR="/home/ubuntu/telegram-ai-system/admin-backend"

echo "===== admin-backend 性能分析 ====="
echo "检查目录: $ADMIN_BACKEND_DIR"
echo ""

# 检查目录是否存在
if [ ! -d "$ADMIN_BACKEND_DIR" ]; then
    echo "❌ 错误: admin-backend 目录不存在: $ADMIN_BACKEND_DIR"
    exit 1
fi

cd "$ADMIN_BACKEND_DIR" || exit 1

echo "=== 1. 检查日志文件 ==="
if [ -d "logs" ]; then
    echo "✓ 找到 logs 目录"
    echo "最近的错误日志:"
    find logs -name "*.log" -type f -mtime -1 -exec ls -lh {} \; 2>/dev/null | head -5
    echo ""
    echo "最近的错误内容 (最后 50 行):"
    find logs -name "*.log" -type f -mtime -1 -exec tail -50 {} \; 2>/dev/null | grep -i "error\|exception\|traceback\|deadlock\|timeout" | tail -20
else
    echo "⚠️  未找到 logs 目录"
fi

echo ""
echo "=== 2. 检查 PM2 日志 ==="
echo "PM2 进程状态:"
pm2 list | grep -E "admin|backend|uvicorn" || echo "未找到相关 PM2 进程"
echo ""
echo "查看 PM2 日志命令:"
echo "  pm2 logs <app_name> --lines 100"
echo "  pm2 logs <app_name> --err --lines 100  # 只看错误"
echo "  pm2 monit  # 实时监控"

echo ""
echo "=== 3. 检查 main.py 和路由文件 ==="
if [ -f "app/main.py" ]; then
    echo "✓ 找到 app/main.py"
    echo ""
    echo "检查同步路由 (可能阻塞主线程):"
    grep -n "def \|async def " app/main.py | head -20
    echo ""
    echo "检查是否有同步的数据库操作:"
    grep -n "\.query\|\.get\|\.all()\|\.first()" app/main.py | head -10
    echo ""
    echo "检查是否有重计算任务:"
    grep -n -i "for.*in.*range\|while.*True\|\.map\|\.filter\|sorted\|\.sort" app/main.py | head -10
else
    echo "❌ 未找到 app/main.py"
fi

# 检查路由文件
if [ -d "app/routers" ] || [ -d "app/api" ] || [ -d "app/routes" ]; then
    echo ""
    echo "检查路由文件:"
    find app -name "*.py" -path "*/routers/*" -o -path "*/api/*" -o -path "*/routes/*" 2>/dev/null | head -10
    for route_file in $(find app -name "*.py" -path "*/routers/*" -o -path "*/api/*" -o -path "*/routes/*" 2>/dev/null | head -5); do
        echo ""
        echo "--- $route_file ---"
        echo "同步函数 (可能阻塞):"
        grep -n "^def " "$route_file" | head -5
        echo "数据库查询 (可能未异步):"
        grep -n "\.query\|\.get\|\.all()\|\.first()" "$route_file" | head -5
    done
fi

echo ""
echo "=== 4. 检查数据库连接配置 ==="
echo "查找数据库配置文件:"
find . -name "*.py" -exec grep -l "create_engine\|SessionLocal\|sessionmaker\|connection.*pool" {} \; 2>/dev/null | head -5

for db_file in $(find . -name "*.py" -exec grep -l "create_engine\|SessionLocal\|sessionmaker" {} \; 2>/dev/null | head -3); do
    echo ""
    echo "--- $db_file ---"
    echo "数据库引擎配置:"
    grep -A 5 "create_engine" "$db_file" | head -10
    echo ""
    echo "连接池配置:"
    grep -i "pool_size\|max_overflow\|pool_pre_ping\|pool_recycle" "$db_file" | head -10
    echo ""
    echo "Session 配置:"
    grep -A 3 "SessionLocal\|sessionmaker" "$db_file" | head -10
done

echo ""
echo "=== 5. 检查是否有 Celery/异步队列配置 ==="
if [ -f "celery_app.py" ] || [ -f "app/celery_app.py" ] || [ -f "tasks.py" ] || [ -f "app/tasks.py" ]; then
    echo "✓ 找到 Celery 配置文件"
    find . -name "*celery*.py" -o -name "tasks.py" 2>/dev/null | head -5
else
    echo "⚠️  未找到 Celery 配置，可能所有任务都在主线程执行"
fi

echo ""
echo "=== 6. 检查依赖文件 ==="
if [ -f "requirements.txt" ]; then
    echo "检查是否安装了异步任务队列:"
    grep -E "celery|rq|dramatiq|huey" requirements.txt || echo "未找到异步任务队列库"
    echo ""
    echo "检查数据库相关库:"
    grep -E "sqlalchemy|asyncpg|aiomysql|databases" requirements.txt || echo "未找到数据库库"
fi

echo ""
echo "=== 7. 检查当前运行的进程 ==="
ps aux | grep -E "uvicorn|gunicorn|python.*main.py" | grep -v grep

echo ""
echo "===== 分析完成 ====="
echo ""
echo "建议的下一步操作:"
echo "1. 查看 PM2 实时日志: pm2 logs <app_name> --lines 200"
echo "2. 检查是否有死循环: 查看日志中是否有重复的错误信息"
echo "3. 检查数据库连接: 查看是否有连接泄漏或未关闭的会话"
echo "4. 检查 CPU 使用: top -p \$(pgrep -f 'uvicorn.*admin')"


