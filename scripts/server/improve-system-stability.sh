#!/bin/bash
# ============================================================
# 改进系统稳定性 - 防止 CPU 100% 和服务崩溃
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
ECOSYSTEM_FILE="$PROJECT_DIR/ecosystem.config.js"
LOGS_DIR="$PROJECT_DIR/logs"

echo "=========================================="
echo "🔧 改进系统稳定性"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 创建日志目录
echo "[1/7] 创建日志目录..."
echo "----------------------------------------"
mkdir -p "$LOGS_DIR"
chown -R ubuntu:ubuntu "$LOGS_DIR"
echo "✅ 日志目录: $LOGS_DIR"
echo ""

# 2. 备份现有配置
echo "[2/7] 备份现有 PM2 配置..."
echo "----------------------------------------"
if [ -f "$ECOSYSTEM_FILE" ]; then
    BACKUP_FILE="${ECOSYSTEM_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$ECOSYSTEM_FILE" "$BACKUP_FILE"
    echo "✅ 配置已备份到: $BACKUP_FILE"
else
    echo "⚠️  配置文件不存在，将创建新配置"
fi
echo ""

# 3. 创建改进的 PM2 配置
echo "[3/7] 创建改进的 PM2 配置..."
echo "----------------------------------------"
cat > "$ECOSYSTEM_FILE" << 'EOF'
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      script: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        PORT: 8000,
        PYTHONPATH: "/home/ubuntu/telegram-ai-system/admin-backend",
        PYTHONUNBUFFERED: "1",
        NODE_ENV: "production"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/backend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      // 自动重启配置
      autorestart: true,
      watch: false,
      // 资源限制（防止 CPU 100%）
      max_memory_restart: "800M",  // 降低内存限制，更早重启
      max_cpu_restart: "80%",      // CPU 超过 80% 自动重启
      // 重启策略
      min_uptime: "30s",           // 至少运行 30 秒才算成功
      max_restarts: 15,            // 最多重启 15 次
      restart_delay: 10000,        // 重启延迟 10 秒
      // 进程管理
      instances: 1,
      exec_mode: "fork",
      // 日志轮转
      log_type: "json",
      // 健康检查
      kill_timeout: 5000,
      wait_ready: false,
      listen_timeout: 10000
    },
    {
      name: "next-server",
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      script: "npm",
      args: "start",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
        // 限制 Node.js 内存使用（防止内存泄漏）
        NODE_OPTIONS: "--max-old-space-size=1024 --max-semi-space-size=128"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/frontend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      // 自动重启配置
      autorestart: true,
      watch: false,
      // 资源限制（防止 CPU 100%）
      max_memory_restart: "800M",  // 降低内存限制
      max_cpu_restart: "80%",      // CPU 超过 80% 自动重启
      // 重启策略
      min_uptime: "30s",           // 至少运行 30 秒才算成功
      max_restarts: 15,            // 最多重启 15 次
      restart_delay: 10000,        // 重启延迟 10 秒
      // 进程管理
      instances: 1,
      exec_mode: "fork",
      // 日志轮转
      log_type: "json",
      // 健康检查
      kill_timeout: 5000,
      wait_ready: false,
      listen_timeout: 10000
    }
  ]
};
EOF

chown ubuntu:ubuntu "$ECOSYSTEM_FILE"
chmod 644 "$ECOSYSTEM_FILE"
echo "✅ PM2 配置已更新"
echo ""

# 4. 配置日志轮转
echo "[4/7] 配置日志轮转..."
echo "----------------------------------------"
cat > /tmp/pm2-logrotate.conf << 'EOF'
/home/ubuntu/telegram-ai-system/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ubuntu ubuntu
    sharedscripts
    postrotate
        pm2 reloadLogs
    endscript
}
EOF

if [ -f /etc/logrotate.d/pm2 ]; then
    sudo mv /etc/logrotate.d/pm2 /etc/logrotate.d/pm2.backup.$(date +%Y%m%d_%H%M%S)
fi

sudo mv /tmp/pm2-logrotate.conf /etc/logrotate.d/pm2
echo "✅ 日志轮转已配置"
echo ""

# 5. 创建监控脚本
echo "[5/7] 创建系统监控脚本..."
echo "----------------------------------------"
cat > "$PROJECT_DIR/scripts/server/monitor-system.sh" << 'MONITOR_EOF'
#!/bin/bash
# 系统监控脚本 - 检测高 CPU 和自动重启

LOG_FILE="/home/ubuntu/telegram-ai-system/logs/monitor.log"
MAX_CPU=90
MAX_MEMORY=90

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查系统 CPU
SYSTEM_CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
if (( $(echo "$SYSTEM_CPU > $MAX_CPU" | bc -l 2>/dev/null || echo "0") )); then
    log_message "⚠️  系统 CPU 使用率过高: ${SYSTEM_CPU}%"
    
    # 查找高 CPU 进程
    HIGH_CPU_PIDS=$(ps aux --sort=-%cpu | awk 'NR>1 && $3>50 && ($11 ~ /next/ || $11 ~ /node/ || $11 ~ /uvicorn/) {print $2}')
    if [ -n "$HIGH_CPU_PIDS" ]; then
        log_message "发现高 CPU 进程: $HIGH_CPU_PIDS"
        for PID in $HIGH_CPU_PIDS; do
            CPU_USAGE=$(ps -p $PID -o %cpu= 2>/dev/null | tr -d ' ')
            if [ -n "$CPU_USAGE" ] && (( $(echo "$CPU_USAGE > 80" | bc -l 2>/dev/null || echo "0") )); then
                log_message "重启高 CPU 进程 PID $PID (CPU: ${CPU_USAGE}%)"
                kill -HUP $PID 2>/dev/null || pm2 restart all
            fi
        done
    fi
fi

# 检查 PM2 进程状态
if command -v pm2 &> /dev/null; then
    ERRORED=$(pm2 jlist 2>/dev/null | jq -r '.[] | select(.pm2_env.status == "errored") | .name' 2>/dev/null || echo "")
    if [ -n "$ERRORED" ]; then
        log_message "⚠️  发现 PM2 错误进程: $ERRORED"
        pm2 restart $ERRORED
    fi
fi
MONITOR_EOF

chmod +x "$PROJECT_DIR/scripts/server/monitor-system.sh"
chown ubuntu:ubuntu "$PROJECT_DIR/scripts/server/monitor-system.sh"
echo "✅ 监控脚本已创建"
echo ""

# 6. 设置定时任务（每 5 分钟检查一次）
echo "[6/7] 设置定时监控任务..."
echo "----------------------------------------"
CRON_JOB="*/5 * * * * /home/ubuntu/telegram-ai-system/scripts/server/monitor-system.sh"
(crontab -u ubuntu -l 2>/dev/null | grep -v "monitor-system.sh"; echo "$CRON_JOB") | crontab -u ubuntu -
echo "✅ 定时监控任务已设置（每 5 分钟检查一次）"
echo ""

# 7. 重启服务
echo "[7/7] 重启服务以应用新配置..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    cd "$PROJECT_DIR"
    sudo -u ubuntu pm2 delete all 2>/dev/null || true
    sleep 2
    sudo -u ubuntu pm2 start ecosystem.config.js
    sleep 5
    sudo -u ubuntu pm2 save
    
    echo "服务状态:"
    sudo -u ubuntu pm2 list
    echo ""
    
    echo "✅ 服务已重启"
else
    echo "⚠️  PM2 未安装"
fi
echo ""

echo "=========================================="
echo "✅ 稳定性改进完成"
echo "=========================================="
echo ""
echo "改进内容："
echo "  1. ✅ 添加 CPU 限制（超过 80% 自动重启）"
echo "  2. ✅ 降低内存限制（800M，更早重启防止内存泄漏）"
echo "  3. ✅ 改进重启策略（延迟 10 秒，最多 15 次）"
echo "  4. ✅ 配置日志轮转（自动清理旧日志）"
echo "  5. ✅ 添加系统监控（每 5 分钟检查一次）"
echo "  6. ✅ 优化 Node.js 内存参数"
echo ""
echo "监控日志: tail -f $LOGS_DIR/monitor.log"
echo "PM2 状态: pm2 list"
echo "PM2 监控: pm2 monit"
echo ""

