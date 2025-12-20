#!/bin/bash
# ============================================================
# 紧急修复高 CPU 使用率问题
# ============================================================

set -e

echo "=========================================="
echo "🚨 紧急修复高 CPU 使用率"
echo "=========================================="
echo ""

# 1. 杀死异常的高 CPU 进程
echo "[1/5] 杀死异常的高 CPU 进程..."
echo "----------------------------------------"

# 查找并杀死异常的 Next.js 进程
HIGH_CPU_PIDS=$(ps aux --sort=-%cpu | awk 'NR>1 && $3>50 && ($11 ~ /next/ || $11 ~ /node/) {print $2}')

if [ -n "$HIGH_CPU_PIDS" ]; then
    echo "发现高 CPU 进程: $HIGH_CPU_PIDS"
    for PID in $HIGH_CPU_PIDS; do
        PROCESS_INFO=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
        echo "  杀死进程 PID $PID ($PROCESS_INFO)..."
        kill -9 $PID 2>/dev/null || echo "    进程 $PID 已不存在"
    done
    echo "✅ 异常进程已终止"
    sleep 2
else
    echo "✅ 未发现异常高 CPU 进程"
fi
echo ""

# 2. 停止所有 PM2 进程
echo "[2/5] 停止所有 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    echo "停止所有 PM2 进程..."
    pm2 stop all 2>/dev/null || true
    sleep 2
    echo "清理 PM2 进程..."
    pm2 kill 2>/dev/null || true
    sleep 1
    echo "✅ PM2 进程已停止"
else
    echo "⚠️  PM2 未安装"
fi
echo ""

# 3. 重启 Nginx
echo "[3/5] 重启 Nginx..."
echo "----------------------------------------"
sudo systemctl stop nginx 2>/dev/null || true
sleep 1
sudo systemctl start nginx
sleep 2

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重启"
else
    echo "❌ Nginx 启动失败"
    sudo systemctl status nginx --no-pager | head -10
fi
echo ""

# 4. 重新启动后端服务
echo "[4/5] 重新启动后端服务..."
echo "----------------------------------------"
cd /home/ubuntu/telegram-ai-system/admin-backend || exit 1

# 确保使用正确的 Python 环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 启动后端
if command -v pm2 &> /dev/null; then
    pm2 start ecosystem.config.js || pm2 restart api
    sleep 3
    echo "✅ 后端服务已启动"
    pm2 list
else
    echo "⚠️  PM2 未安装，无法启动后端"
fi
echo ""

# 5. 重新启动前端服务
echo "[5/5] 重新启动前端服务..."
echo "----------------------------------------"
cd /home/ubuntu/telegram-ai-system/saas-demo || exit 1

# 检查是否有 .next 目录
if [ ! -d ".next" ]; then
    echo "⚠️  .next 目录不存在，需要重新构建"
    echo "   这可能需要几分钟..."
    npm run build
fi

# 启动前端
if command -v pm2 &> /dev/null; then
    pm2 start npm --name next-server -- start || pm2 restart next-server
    sleep 5
    echo "✅ 前端服务已启动"
    pm2 list
else
    echo "⚠️  PM2 未安装，无法启动前端"
fi
echo ""

# 6. 等待并检查服务状态
echo "等待服务稳定..."
sleep 5

echo ""
echo "检查服务状态..."
echo "----------------------------------------"

# 检查端口
if sudo ss -tlnp | grep -q ":3000 "; then
    echo "✅ 前端服务 (端口 3000) 正在运行"
else
    echo "❌ 前端服务 (端口 3000) 未运行"
fi

if sudo ss -tlnp | grep -q ":8000 "; then
    echo "✅ 后端服务 (端口 8000) 正在运行"
else
    echo "❌ 后端服务 (端口 8000) 未运行"
fi

# 检查 CPU 使用率
echo ""
echo "当前 CPU 使用率 (top 5):"
ps aux --sort=-%cpu | head -6 | awk '{printf "%-8s %6s %-s\n", $2, $3"%", $11}'

CURRENT_CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
echo ""
echo "系统总体 CPU 使用率: ${CURRENT_CPU}%"

if (( $(echo "$CURRENT_CPU > 50" | bc -l 2>/dev/null || echo "0") )); then
    echo "⚠️  CPU 使用率仍然较高，请继续监控"
else
    echo "✅ CPU 使用率已恢复正常"
fi
echo ""

# 测试服务连接
echo "测试服务连接..."
if curl -s http://127.0.0.1:3000 > /dev/null; then
    echo "✅ 前端服务可以响应"
else
    echo "⚠️  前端服务无法响应（可能正在启动中）"
fi

if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ 后端服务可以响应"
else
    echo "⚠️  后端服务无法响应（可能正在启动中）"
fi
echo ""

echo "=========================================="
echo "✅ 紧急修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请："
echo "  1. 检查 PM2 日志: pm2 logs"
echo "  2. 检查 Nginx 日志: sudo tail -f /var/log/nginx/error.log"
echo "  3. 考虑重启服务器"
echo ""

