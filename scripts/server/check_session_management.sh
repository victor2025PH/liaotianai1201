#!/bin/bash
# Session 文件管理功能排查脚本

WORKER_ID="${1:-PC-001}"
echo "=========================================="
echo "Session 文件管理功能排查"
echo "Worker ID: $WORKER_ID"
echo "=========================================="
echo ""

echo "[1/5] 检查后端服务状态"
echo "----------------------------------------"
if systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务运行中"
    sudo systemctl status luckyred-api --no-pager | head -7
else
    echo "❌ 后端服务未运行"
    sudo systemctl status luckyred-api --no-pager | head -7
fi
echo ""

echo "[2/5] 检查后端日志（最近 20 行，包含 sessions）"
echo "----------------------------------------"
SESSION_LOGS=$(sudo journalctl -u luckyred-api -n 50 --no-pager 2>/dev/null | grep -i "session\|worker" | tail -20)
if [ -n "$SESSION_LOGS" ]; then
    echo "$SESSION_LOGS"
else
    echo "⚠️  未找到相关日志"
fi
echo ""

echo "[3/5] 检查 Redis 服务状态"
echo "----------------------------------------"
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis 服务运行中"
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis 连接正常"
    else
        echo "❌ Redis 连接失败"
    fi
else
    echo "❌ Redis 服务未运行"
fi
echo ""

echo "[4/5] 检查 Worker 节点状态"
echo "----------------------------------------"
if command -v redis-cli > /dev/null 2>&1 && redis-cli ping > /dev/null 2>&1; then
    WORKER_DATA=$(redis-cli GET "worker:node:$WORKER_ID" 2>/dev/null)
    if [ -n "$WORKER_DATA" ]; then
        WORKER_STATUS=$(echo "$WORKER_DATA" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        LAST_HEARTBEAT=$(echo "$WORKER_DATA" | grep -o '"last_heartbeat":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
        echo "Worker 状态: $WORKER_STATUS"
        echo "最后心跳: $LAST_HEARTBEAT"
    else
        echo "⚠️  Worker 节点 $WORKER_ID 不在 Redis 中"
    fi
    
    echo ""
    echo "所有在线 Worker 节点:"
    redis-cli SMEMBERS worker:nodes:all 2>/dev/null | head -10 || echo "无节点"
else
    echo "⚠️  Redis 不可用，无法检查 Worker 节点状态"
fi
echo ""

echo "[5/5] 检查命令队列"
echo "----------------------------------------"
if command -v redis-cli > /dev/null 2>&1 && redis-cli ping > /dev/null 2>&1; then
    QUEUE_LEN=$(redis-cli LLEN "worker:commands:$WORKER_ID" 2>/dev/null || echo "0")
    echo "命令队列长度: $QUEUE_LEN"
    if [ "$QUEUE_LEN" -gt 0 ]; then
        echo "队列内容（最近 3 条）:"
        redis-cli LRANGE "worker:commands:$WORKER_ID" 0 2 2>/dev/null | head -3
    else
        echo "队列为空"
    fi
    
    echo ""
    echo "响应存储（最近 5 个）:"
    RESPONSE_KEYS=$(redis-cli KEYS "worker:response:$WORKER_ID:*" 2>/dev/null | head -5)
    if [ -n "$RESPONSE_KEYS" ]; then
        echo "$RESPONSE_KEYS"
    else
        echo "无响应存储"
    fi
else
    echo "⚠️  Redis 不可用，无法检查命令队列"
fi
echo ""

echo "=========================================="
echo "排查完成"
echo "=========================================="
echo ""
echo "提示："
echo "1. 如果后端服务未运行，执行: sudo systemctl start luckyred-api"
echo "2. 如果 Redis 未运行，执行: sudo systemctl start redis-server"
echo "3. 查看详细日志: sudo journalctl -u luckyred-api -f"
echo "4. 查看 Worker 节点日志: 检查 Worker 节点的日志文件"

