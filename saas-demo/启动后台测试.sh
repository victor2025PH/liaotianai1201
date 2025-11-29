#!/bin/bash
# 启动后台测试任务

LOG_DIR="$HOME/liaotian/test_logs"
mkdir -p "$LOG_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SCRIPT="$SCRIPT_DIR/后台执行测试.sh"

# 检查脚本是否存在
if [ ! -f "$BACKEND_SCRIPT" ]; then
    echo "错误: 找不到 后台执行测试.sh"
    exit 1
fi

# 给脚本添加执行权限
chmod +x "$BACKEND_SCRIPT"

# 使用 nohup 在后台执行
echo "========================================"
echo "启动后台测试任务"
echo "========================================"
echo ""

nohup bash "$BACKEND_SCRIPT" > /dev/null 2>&1 &

PID=$!
echo "✅ 测试任务已在后台启动"
echo "进程 ID: $PID"
echo ""

# 保存 PID
echo "$PID" > "$LOG_DIR/e2e_test.pid"

echo "查看实时日志:"
echo "  tail -f $LOG_DIR/e2e_test_*.log"
echo ""
echo "查看最新日志:"
echo "  ls -lt $LOG_DIR/e2e_test_*.log | head -1 | awk '{print \$NF}' | xargs tail -f"
echo ""
echo "停止测试任务:"
echo "  kill $PID"
echo ""

# 等待一秒，然后显示日志文件
sleep 1
LATEST_LOG=$(ls -t "$LOG_DIR"/e2e_test_*.log 2>/dev/null | head -1)

if [ -n "$LATEST_LOG" ]; then
    echo "最新的日志文件: $LATEST_LOG"
    echo ""
    echo "显示最新日志（前 20 行）:"
    echo "----------------------------------------"
    tail -20 "$LATEST_LOG" 2>/dev/null || echo "日志文件尚未创建"
else
    echo "日志文件将保存到: $LOG_DIR/e2e_test_*.log"
fi

echo ""
echo "使用以下命令查看实时进度:"
echo "  tail -f $LOG_DIR/e2e_test_*.log"
