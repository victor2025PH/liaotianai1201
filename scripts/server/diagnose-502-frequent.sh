#!/bin/bash
# ============================================================
# 诊断频繁 502 错误脚本
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔍 诊断频繁 502 Bad Gateway 错误"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="luckyred-api"
BACKEND_PORT=8000

# 1. 检查后端服务状态
echo "[1/8] 检查后端服务状态..."
echo "----------------------------------------"
if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "✅ 后端服务 ($BACKEND_SERVICE) 正在运行"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -15
else
    echo "❌ 后端服务 ($BACKEND_SERVICE) 未运行"
    echo "尝试查看服务状态:"
    systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
fi
echo ""

# 2. 检查服务重启频率（最近1小时）
echo "[2/8] 检查服务重启频率（最近1小时）..."
echo "----------------------------------------"
RESTART_COUNT=$(journalctl -u "$BACKEND_SERVICE" --since "1 hour ago" --no-pager | grep -c "Started\|Stopped" || echo "0")
if [ "$RESTART_COUNT" -gt 5 ]; then
    echo "⚠️  警告: 服务在最近1小时内重启了 $RESTART_COUNT 次（可能频繁崩溃）"
    echo "最近的重启记录:"
    journalctl -u "$BACKEND_SERVICE" --since "1 hour ago" --no-pager | grep "Started\|Stopped" | tail -10
else
    echo "✅ 服务重启频率正常（最近1小时: $RESTART_COUNT 次）"
fi
echo ""

# 3. 检查端口监听
echo "[3/8] 检查端口 $BACKEND_PORT 监听状态..."
echo "----------------------------------------"
if ss -tlnp | grep -q ":$BACKEND_PORT "; then
    echo "✅ 端口 $BACKEND_PORT 正在监听"
    ss -tlnp | grep ":$BACKEND_PORT " | head -3
else
    echo "❌ 端口 $BACKEND_PORT 未监听（后端服务可能未启动或崩溃）"
fi
echo ""

# 4. 检查后端进程
echo "[4/8] 检查后端进程..."
echo "----------------------------------------"
BACKEND_PIDS=$(pgrep -f "uvicorn\|gunicorn\|python.*main.py" | head -5)
if [ -n "$BACKEND_PIDS" ]; then
    echo "✅ 发现后端进程:"
    ps aux | grep -E "uvicorn|gunicorn|python.*main.py" | grep -v grep | head -5
else
    echo "❌ 未发现后端进程"
fi
echo ""

# 5. 检查最近的错误日志
echo "[5/8] 检查最近的错误日志（最近50行）..."
echo "----------------------------------------"
ERROR_LOG=$(journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | grep -iE "error|exception|traceback|failed|crash" | tail -10)
if [ -n "$ERROR_LOG" ]; then
    echo "⚠️  发现错误日志:"
    echo "$ERROR_LOG"
else
    echo "✅ 未发现明显的错误日志"
fi
echo ""

# 6. 检查内存使用
echo "[6/8] 检查内存使用情况..."
echo "----------------------------------------"
MEMORY_USAGE=$(free -h | grep Mem | awk '{print $3 "/" $2}')
MEMORY_PERCENT=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
echo "当前内存使用: $MEMORY_USAGE ($MEMORY_PERCENT%)"
if [ "$MEMORY_PERCENT" -gt 90 ]; then
    echo "⚠️  警告: 内存使用率过高（$MEMORY_PERCENT%），可能导致 OOM 杀死进程"
    echo "检查是否有进程被 OOM 杀死:"
    dmesg | grep -i "out of memory\|oom" | tail -5
fi
echo ""

# 7. 检查 CPU 使用
echo "[7/8] 检查 CPU 使用情况..."
echo "----------------------------------------"
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
echo "当前 CPU 使用率: ${CPU_USAGE}%"
if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
    echo "⚠️  警告: CPU 使用率过高（${CPU_USAGE}%），可能导致响应超时"
    echo "CPU 使用率最高的进程:"
    ps aux --sort=-%cpu | head -6
fi
echo ""

# 8. 检查 Nginx 配置和状态
echo "[8/8] 检查 Nginx 配置和状态..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
    if nginx -t 2>&1 | grep -q "successful"; then
        echo "✅ Nginx 配置语法正确"
    else
        echo "❌ Nginx 配置语法错误:"
        nginx -t 2>&1
    fi
    
    # 检查 Nginx 错误日志
    NGINX_ERROR_LOG="/var/log/nginx/error.log"
    if [ -f "$NGINX_ERROR_LOG" ]; then
        RECENT_502=$(tail -100 "$NGINX_ERROR_LOG" | grep -c "502\|upstream\|connect.*failed" || echo "0")
        if [ "$RECENT_502" -gt 0 ]; then
            echo "⚠️  发现 $RECENT_502 个 502 相关错误（最近100行）"
            echo "最近的 502 错误:"
            tail -100 "$NGINX_ERROR_LOG" | grep -i "502\|upstream\|connect.*failed" | tail -5
        else
            echo "✅ Nginx 错误日志中未发现 502 相关错误"
        fi
    fi
else
    echo "❌ Nginx 未运行"
fi
echo ""

# 总结和建议
echo "=========================================="
echo "📋 诊断总结"
echo "=========================================="
echo ""

ISSUES_FOUND=0

if ! systemctl is-active --quiet "$BACKEND_SERVICE"; then
    echo "❌ 问题 1: 后端服务未运行"
    echo "   解决方案: sudo systemctl start $BACKEND_SERVICE"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if ! ss -tlnp | grep -q ":$BACKEND_PORT "; then
    echo "❌ 问题 2: 端口 $BACKEND_PORT 未监听"
    echo "   解决方案: 检查后端服务是否启动，或端口是否被占用"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$RESTART_COUNT" -gt 5 ]; then
    echo "⚠️  问题 3: 服务频繁重启（可能崩溃）"
    echo "   解决方案: 查看详细日志: sudo journalctl -u $BACKEND_SERVICE -n 100"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$MEMORY_PERCENT" -gt 90 ]; then
    echo "⚠️  问题 4: 内存使用率过高"
    echo "   解决方案: 清理内存或增加服务器内存"
    ISSUES_FOUND=$((ISSUES_FOUND+1))
fi

if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo "✅ 未发现明显问题"
    echo ""
    echo "如果仍然出现 502 错误，请检查:"
    echo "1. Nginx 配置中的 upstream 地址是否正确"
    echo "2. 后端服务响应时间是否过长（超时）"
    echo "3. 防火墙是否阻止了连接"
    echo "4. 查看详细日志: sudo journalctl -u $BACKEND_SERVICE -n 200"
else
    echo ""
    echo "发现 $ISSUES_FOUND 个问题，建议先解决这些问题"
fi

echo ""
echo "=========================================="
echo ""

