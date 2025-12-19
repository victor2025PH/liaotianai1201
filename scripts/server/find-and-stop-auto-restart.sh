#!/bin/bash
# ============================================================
# 查找并停止自动重启 next-server 的机制
# ============================================================

echo "=========================================="
echo "🔍 查找并停止自动重启 next-server 的机制"
echo "=========================================="
echo ""

# 1. 检查 deployer 用户的 PM2 进程
echo "[1/6] 检查 deployer 用户的 PM2 进程..."
echo "----------------------------------------"
if sudo -u deployer pm2 list 2>/dev/null | grep -q "next-server\|frontend"; then
    echo "⚠️  发现 deployer 用户的 PM2 进程！"
    sudo -u deployer pm2 list
    echo ""
    echo "停止 deployer 用户的 PM2 进程..."
    sudo -u deployer pm2 stop all 2>/dev/null || true
    sudo -u deployer pm2 delete all 2>/dev/null || true
    echo "✅ 已停止 deployer 用户的 PM2 进程"
else
    echo "✅ 未发现 deployer 用户的 PM2 进程"
fi
echo ""

# 2. 检查 systemd 服务（包括所有用户）
echo "[2/6] 检查所有 systemd 前端服务..."
echo "----------------------------------------"
SYSTEMD_SERVICES=$(systemctl list-units --type=service --all 2>/dev/null | grep -E "frontend|next-server|node.*3000" || echo "")
if [ -n "$SYSTEMD_SERVICES" ]; then
    echo "⚠️  发现可能的 systemd 服务:"
    echo "$SYSTEMD_SERVICES"
    echo ""
    # 尝试停止这些服务
    for service in $(echo "$SYSTEMD_SERVICES" | awk '{print $1}'); do
        if [ -n "$service" ]; then
            echo "  停止服务: $service"
            sudo systemctl stop "$service" 2>/dev/null || true
            sudo systemctl disable "$service" 2>/dev/null || true
        fi
    done
else
    echo "✅ 未发现相关的 systemd 服务"
fi
echo ""

# 3. 检查 supervisor
echo "[3/6] 检查 supervisor..."
echo "----------------------------------------"
if command -v supervisorctl >/dev/null 2>&1; then
    echo "⚠️  发现 supervisor"
    sudo supervisorctl status 2>/dev/null | grep -E "next-server|frontend|3000" || echo "  未发现相关进程"
    # 停止相关进程
    sudo supervisorctl stop all 2>/dev/null || true
else
    echo "✅ 未安装 supervisor"
fi
echo ""

# 4. 检查 cron 任务
echo "[4/6] 检查 cron 任务..."
echo "----------------------------------------"
CRON_JOBS=$(crontab -l 2>/dev/null | grep -E "next-server|3000|pm2.*frontend" || echo "")
if [ -n "$CRON_JOBS" ]; then
    echo "⚠️  发现可能的 cron 任务:"
    echo "$CRON_JOBS"
else
    echo "✅ 未发现相关的 cron 任务"
fi

# 检查所有用户的 crontab
for user in ubuntu deployer root; do
    USER_CRON=$(sudo crontab -u $user -l 2>/dev/null | grep -E "next-server|3000|pm2.*frontend" || echo "")
    if [ -n "$USER_CRON" ]; then
        echo "⚠️  发现 $user 用户的 cron 任务:"
        echo "$USER_CRON"
    fi
done
echo ""

# 5. 检查是否有监控脚本在运行
echo "[5/6] 检查监控脚本..."
echo "----------------------------------------"
MONITOR_SCRIPTS=$(ps aux | grep -E "watch|monitor|restart.*frontend|restart.*next" | grep -v grep || echo "")
if [ -n "$MONITOR_SCRIPTS" ]; then
    echo "⚠️  发现可能的监控脚本:"
    echo "$MONITOR_SCRIPTS"
    # 杀掉这些脚本
    for pid in $(echo "$MONITOR_SCRIPTS" | awk '{print $2}'); do
        echo "  杀掉监控脚本 PID: $pid"
        sudo kill -9 $pid 2>/dev/null || true
    done
else
    echo "✅ 未发现监控脚本"
fi
echo ""

# 6. 检查 next-server 的父进程
echo "[6/6] 检查 next-server 的父进程..."
echo "----------------------------------------"
NEXT_PID=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " | grep -oP 'pid=\K\d+' | head -1 || echo "")
if [ -n "$NEXT_PID" ]; then
    echo "当前占用端口 3000 的进程 PID: $NEXT_PID"
    PPID=$(ps -o ppid= -p $NEXT_PID 2>/dev/null | tr -d ' ' || echo "")
    if [ -n "$PPID" ]; then
        echo "父进程 PID: $PPID"
        PARENT_INFO=$(ps -fp $PPID -o pid,ppid,user,comm,args 2>/dev/null || echo "")
        if [ -n "$PARENT_INFO" ]; then
            echo "父进程信息:"
            echo "$PARENT_INFO"
            
            # 如果父进程是 systemd (PID 1)，说明是系统服务
            if [ "$PPID" = "1" ]; then
                echo ""
                echo "⚠️  父进程是 systemd (PID 1)，说明是系统服务"
                echo "尝试查找服务名..."
                SERVICE_NAME=$(sudo systemctl status $NEXT_PID 2>/dev/null | grep -o "Loaded: loaded (/.*" | awk '{print $3}' | xargs basename 2>/dev/null | cut -d';' -f1 || echo "")
                if [ -n "$SERVICE_NAME" ]; then
                    echo "  服务名: $SERVICE_NAME"
                    echo "  停止服务..."
                    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
                    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
                fi
            fi
        fi
    fi
else
    echo "✅ 端口 3000 当前未被占用"
fi
echo ""

echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请执行："
echo "1. 杀掉所有 next-server 进程: sudo pkill -9 -f 'next-server'"
echo "2. 检查是否有其他进程管理器: ps aux | grep -E 'pm2|supervisor|systemd'"
echo "3. 查看所有用户的进程: ps aux | grep deployer"

