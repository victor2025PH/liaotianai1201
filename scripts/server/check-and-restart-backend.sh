#!/bin/bash
# ============================================================
# 检查并重启后端服务脚本
# 用于在更新 Redis 密码后重启后端
# ============================================================

echo "=========================================="
echo "检查并重启后端服务"
echo "=========================================="
echo ""

# 1. 检查 PM2 进程
echo "[1] 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
    echo "PM2 已安装"
    echo ""
    echo "当前 PM2 进程列表："
    pm2 list
    echo ""
    
    # 查找可能的后端进程
    PM2_PROCESSES=$(pm2 list | grep -E "online|stopped" | awk '{print $2}' | grep -v "name")
    
    if [ -n "$PM2_PROCESSES" ]; then
        echo "找到以下 PM2 进程："
        for proc in $PM2_PROCESSES; do
            echo "  - $proc"
        done
        echo ""
        echo "请选择要重启的进程名称，或按 Enter 跳过 PM2："
        read -r PM2_NAME
        
        if [ -n "$PM2_NAME" ]; then
            echo "重启 PM2 进程: $PM2_NAME"
            pm2 restart "$PM2_NAME" --update-env
            sleep 3
            pm2 list | grep "$PM2_NAME"
        fi
    else
        echo "未找到运行中的 PM2 进程"
    fi
else
    echo "PM2 未安装"
fi
echo ""

# 2. 检查 systemd 服务
echo "[2] 检查 systemd 服务..."
echo "----------------------------------------"
echo "查找可能的后端服务..."

# 常见的服务名称
POSSIBLE_SERVICES=(
    "luckyred-api"
    "liaotian-api"
    "telegram-ai-backend"
    "admin-backend"
    "backend"
    "api"
)

FOUND_SERVICES=()
for service in "${POSSIBLE_SERVICES[@]}"; do
    if systemctl list-unit-files | grep -q "^${service}.service"; then
        FOUND_SERVICES+=("$service")
    fi
done

# 也检查所有包含 api 或 backend 的服务
ALL_SERVICES=$(systemctl list-unit-files --type=service | grep -E "api|backend" | awk '{print $1}')

if [ -n "$ALL_SERVICES" ]; then
    echo "找到以下可能的后端服务："
    echo "$ALL_SERVICES" | while read -r svc; do
        echo "  - $svc"
    done
    echo ""
    
    # 尝试重启找到的服务
    for svc in "${FOUND_SERVICES[@]}"; do
        echo "尝试重启服务: ${svc}.service"
        if sudo systemctl restart "${svc}.service" 2>/dev/null; then
            sleep 2
            if sudo systemctl is-active --quiet "${svc}.service"; then
                echo "  ✅ ${svc}.service 已重启"
                sudo systemctl status "${svc}.service" --no-pager -l | head -10
            else
                echo "  ⚠️  ${svc}.service 重启后未运行"
            fi
        fi
    done
else
    echo "未找到明显的后端服务"
fi
echo ""

# 3. 检查 Python 进程
echo "[3] 检查 Python 后端进程..."
echo "----------------------------------------"
PYTHON_PROCS=$(ps aux | grep -E "uvicorn|gunicorn|python.*main.py|python.*app.py" | grep -v grep)
if [ -n "$PYTHON_PROCS" ]; then
    echo "找到以下 Python 后端进程："
    echo "$PYTHON_PROCS"
    echo ""
    echo "⚠️  如果使用手动启动的进程，需要手动重启"
    echo "   1. 找到进程 PID"
    echo "   2. kill <PID>"
    echo "   3. 重新启动应用"
else
    echo "未找到运行中的 Python 后端进程"
fi
echo ""

# 4. 检查 Redis 连接
echo "[4] 测试 Redis 连接..."
echo "----------------------------------------"
if [ -f ".env" ]; then
    REDIS_PASSWORD=$(grep "^REDIS_PASSWORD=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ -n "$REDIS_PASSWORD" ]; then
        echo "从 .env 文件读取到 Redis 密码"
        echo "测试 Redis 连接..."
        if redis-cli -a "$REDIS_PASSWORD" -h 127.0.0.1 PING 2>/dev/null | grep -q "PONG"; then
            echo "  ✅ Redis 连接成功"
        else
            echo "  ❌ Redis 连接失败，请检查密码和配置"
        fi
    else
        echo "  ⚠️  未在 .env 文件中找到 REDIS_PASSWORD"
    fi
else
    echo "  ⚠️  未找到 .env 文件"
fi
echo ""

# 5. 检查应用日志
echo "[5] 检查应用日志（最近错误）..."
echo "----------------------------------------"
if [ -d "admin-backend" ]; then
    echo "查找日志文件..."
    find admin-backend -name "*.log" -type f 2>/dev/null | head -5 | while read -r logfile; do
        echo "  - $logfile"
        tail -5 "$logfile" 2>/dev/null | grep -i "error\|redis\|connection" || true
    done
fi

# PM2 日志
if command -v pm2 >/dev/null 2>&1; then
    echo ""
    echo "PM2 日志（最近错误）:"
    pm2 logs --lines 10 --nostream 2>/dev/null | grep -i "error\|redis\|connection" || echo "  无相关错误"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "如果后端服务未找到，可能需要："
echo "  1. 手动启动后端服务"
echo "  2. 检查启动脚本或文档"
echo "  3. 查看项目根目录的 README 或部署文档"
echo ""
