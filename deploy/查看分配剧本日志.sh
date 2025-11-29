#!/bin/bash
# 查看分配剧本相关的日志

echo "=== 查看分配剧本日志 ==="
echo ""

LOG_FILE="/tmp/backend_final.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "⚠ 日志文件不存在: $LOG_FILE"
    echo "尝试使用标准日志文件..."
    LOG_FILE="~/liaotian/admin-backend/logs/backend.log"
fi

echo "查看最近的 PUT 请求日志..."
echo ""
tail -200 "$LOG_FILE" 2>/dev/null | grep -E "MIDDLEWARE|UPDATE_ACCOUNT|639277358115|server_id|不存在" | tail -50

echo ""
echo "=== 完整日志（最后100行）==="
echo ""
tail -100 "$LOG_FILE" 2>/dev/null

echo ""
echo "=== 实时监控日志 ==="
echo "运行以下命令实时查看日志："
echo "  tail -f $LOG_FILE | grep -E \"MIDDLEWARE|UPDATE_ACCOUNT|server_id\""
