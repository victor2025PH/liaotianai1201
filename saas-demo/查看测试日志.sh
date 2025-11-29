#!/bin/bash
# 查看测试日志脚本

LOG_DIR="$HOME/liaotian/test_logs"

# 显示菜单
show_menu() {
    echo "========================================"
    echo "E2E 测试日志查看工具"
    echo "========================================"
    echo ""
    echo "1. 查看最新日志（实时）"
    echo "2. 查看最新日志（最后 50 行）"
    echo "3. 查看所有日志文件"
    echo "4. 查看测试进程状态"
    echo "5. 停止测试进程"
    echo "6. 退出"
    echo ""
}

# 查看实时日志
view_realtime() {
    LATEST_LOG=$(ls -t "$LOG_DIR"/e2e_test_*.log 2>/dev/null | head -1)
    if [ -z "$LATEST_LOG" ]; then
        echo "❌ 没有找到日志文件"
        return
    fi
    echo "查看实时日志: $LATEST_LOG"
    echo "按 Ctrl+C 退出"
    echo "----------------------------------------"
    tail -f "$LATEST_LOG"
}

# 查看最新日志的最后几行
view_tail() {
    LATEST_LOG=$(ls -t "$LOG_DIR"/e2e_test_*.log 2>/dev/null | head -1)
    if [ -z "$LATEST_LOG" ]; then
        echo "❌ 没有找到日志文件"
        return
    fi
    echo "最新日志文件: $LATEST_LOG"
    echo "最后 50 行:"
    echo "----------------------------------------"
    tail -50 "$LATEST_LOG"
}

# 列出所有日志文件
list_logs() {
    if [ ! -d "$LOG_DIR" ]; then
        echo "❌ 日志目录不存在"
        return
    fi
    
    LOGS=$(ls -lt "$LOG_DIR"/e2e_test_*.log 2>/dev/null)
    if [ -z "$LOGS" ]; then
        echo "❌ 没有找到日志文件"
        return
    fi
    
    echo "所有日志文件:"
    echo "----------------------------------------"
    ls -lht "$LOG_DIR"/e2e_test_*.log | awk '{print $9, "(" $5 ")", $6, $7, $8}'
}

# 查看进程状态
check_status() {
    PID_FILE="$LOG_DIR/e2e_test.pid"
    
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ 没有运行中的测试进程"
        return
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ 测试进程正在运行"
        echo "进程 ID: $PID"
        echo ""
        echo "进程信息:"
        ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem
    else
        echo "❌ 进程不存在（可能已完成）"
        rm -f "$PID_FILE"
    fi
}

# 停止测试进程
stop_test() {
    PID_FILE="$LOG_DIR/e2e_test.pid"
    
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ 没有运行中的测试进程"
        return
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "正在停止测试进程 (PID: $PID)..."
        kill "$PID"
        sleep 2
        
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "进程仍在运行，强制停止..."
            kill -9 "$PID"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ 测试进程已停止"
    else
        echo "❌ 进程不存在"
        rm -f "$PID_FILE"
    fi
}

# 主循环
if [ "$1" != "" ]; then
    case "$1" in
        1|realtime|tail)
            view_realtime
            ;;
        2|tail|latest)
            view_tail
            ;;
        3|list)
            list_logs
            ;;
        4|status)
            check_status
            ;;
        5|stop)
            stop_test
            ;;
        *)
            echo "用法: $0 [1|2|3|4|5|realtime|tail|list|status|stop]"
            exit 1
            ;;
    esac
    exit 0
fi

# 交互式菜单
while true; do
    show_menu
    read -p "请选择 [1-6]: " choice
    
    case $choice in
        1)
            view_realtime
            ;;
        2)
            view_tail
            ;;
        3)
            list_logs
            ;;
        4)
            check_status
            ;;
        5)
            stop_test
            ;;
        6|q|exit)
            echo "退出"
            exit 0
            ;;
        *)
            echo "无效选择，请重新输入"
            ;;
    esac
    
    echo ""
    read -p "按 Enter 继续..."
    clear
done
