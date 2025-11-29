#!/bin/bash
# 使用 screen 会话执行测试，便于监控

SESSION_NAME="e2e_test_monitor"
SCRIPT_PATH="$HOME/liaotian/saas-demo/直接执行并反馈.sh"
LOG_FILE="$HOME/liaotian/test_logs/screen_execution_$(date +%Y%m%d_%H%M%S).log"

echo "========================================"
echo "使用 Screen 会话执行测试"
echo "========================================"
echo ""

# 检查 screen 是否安装
if ! command -v screen &> /dev/null; then
    echo "安装 screen..."
    sudo apt-get update && sudo apt-get install -y screen
fi

# 检查会话是否已存在
if screen -list | grep -q "$SESSION_NAME"; then
    echo "会话已存在，先关闭..."
    screen -S "$SESSION_NAME" -X quit
    sleep 2
fi

# 创建新的 screen 会话并执行脚本
echo "创建 screen 会话: $SESSION_NAME"
screen -dmS "$SESSION_NAME" bash -c "bash '$SCRIPT_PATH' 2>&1 | tee '$LOG_FILE'"

echo "✅ 会话已创建"
echo ""
echo "查看会话:"
echo "  screen -r $SESSION_NAME"
echo ""
echo "分离会话: Ctrl+A 然后按 D"
echo ""
echo "查看日志:"
echo "  tail -f $LOG_FILE"
echo ""

# 等待一下然后显示日志
sleep 3
echo "初始日志:"
echo "----------------------------------------"
tail -20 "$LOG_FILE" 2>/dev/null || echo "日志文件尚未生成"
echo "----------------------------------------"
