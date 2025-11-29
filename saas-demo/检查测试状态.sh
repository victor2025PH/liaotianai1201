#!/bin/bash
# 检查测试状态并反馈

LOG_DIR="$HOME/liaotian/test_logs"
mkdir -p "$LOG_DIR"

echo "========================================"
echo "测试状态检查 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 1. 检查后端服务
echo "[1] 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health)
    echo "✅ 后端服务运行正常: $HEALTH"
else
    echo "❌ 后端服务未运行"
fi
echo ""

# 2. 检查测试用户
echo "[2] 检查测试用户..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123" 2>&1)

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ 测试用户登录成功"
else
    echo "❌ 测试用户登录失败: ${LOGIN_RESPONSE:0:100}"
fi
echo ""

# 3. 检查测试进程
echo "[3] 检查测试进程..."
PID_FILE="$LOG_DIR/e2e_test.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ 测试正在运行 (PID: $PID)"
        echo "   进程运行时间: $(ps -p $PID -o etime= | tr -d ' ')"
    else
        echo "❌ 测试进程不存在（可能已完成）"
    fi
else
    echo "⚠️  没有运行中的测试进程"
fi
echo ""

# 4. 检查日志文件
echo "[4] 检查测试日志..."
LATEST_LOG=$(ls -t "$LOG_DIR"/e2e_test_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "✅ 找到日志文件: $LATEST_LOG"
    LOG_SIZE=$(stat -f%z "$LATEST_LOG" 2>/dev/null || stat -c%s "$LATEST_LOG" 2>/dev/null)
    echo "   文件大小: $LOG_SIZE 字节"
    echo ""
    echo "最后 20 行日志:"
    echo "----------------------------------------"
    tail -20 "$LATEST_LOG"
    echo "----------------------------------------"
    
    # 检查是否完成
    if tail -50 "$LATEST_LOG" | grep -qiE "测试.*完成|所有.*完成|测试执行完成"; then
        echo ""
        echo "========================================"
        echo "✅ 测试已完成！"
        echo "========================================"
        
        # 检查是否成功
        if tail -50 "$LATEST_LOG" | grep -qiE "所有测试通过|✅.*成功|测试.*成功"; then
            echo "✅ 测试成功！"
            exit 0
        elif tail -50 "$LATEST_LOG" | grep -qiE "测试失败|❌|错误"; then
            echo "❌ 测试失败"
            echo ""
            echo "错误信息:"
            grep -iE "error|失败|错误|failed" "$LATEST_LOG" | tail -10
            exit 1
        else
            echo "⚠️  测试状态未知"
            exit 2
        fi
    else
        echo ""
        echo "⚠️  测试仍在进行中..."
        exit 2
    fi
else
    echo "❌ 日志文件不存在"
    exit 1
fi
