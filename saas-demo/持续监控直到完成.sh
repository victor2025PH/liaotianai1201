#!/bin/bash
# 持续监控直到所有任务完成

LOG_DIR="$HOME/liaotian/test_logs"
mkdir -p "$LOG_DIR"

# 首先确保准备工作完成
echo "========================================"
echo "开始自动执行和监控"
echo "========================================"
echo ""

# 1. 准备环境
echo "[准备] 更新代码..."
cd ~/liaotian/saas-demo
git pull origin master > /dev/null 2>&1
chmod +x *.sh 2>/dev/null || true

# 2. 检查后端服务
echo "[检查] 后端服务..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ 后端服务未运行，请先启动后端服务"
    echo "启动命令: cd ~/liaotian/admin-backend && source .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi
echo "✅ 后端服务运行正常"

# 3. 准备测试用户
echo "[准备] 测试用户..."
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true
export ADMIN_DEFAULT_PASSWORD=testpass123
python reset_admin_user.py > /dev/null 2>&1
sleep 2

# 验证登录
LOGIN_TEST=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123")

if echo "$LOGIN_TEST" | grep -q "access_token"; then
    echo "✅ 测试用户登录正常"
else
    echo "❌ 测试用户登录失败，尝试修复..."
    python reset_admin_user.py
    sleep 2
fi

# 4. 启动测试（如果未运行）
echo "[启动] 测试任务..."
cd ~/liaotian/saas-demo

PID_FILE="$LOG_DIR/e2e_test.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ 测试已在运行 (PID: $PID)"
    else
        echo "启动新的测试..."
        bash 启动后台测试.sh > /dev/null 2>&1 &
        sleep 3
    fi
else
    echo "启动新的测试..."
    bash 启动后台测试.sh > /dev/null 2>&1 &
    sleep 3
fi

# 5. 持续监控
echo ""
echo "========================================"
echo "开始持续监控（每 15 秒检查一次）"
echo "========================================"
echo ""

CHECK_COUNT=0
MAX_CHECKS=120  # 最多检查30分钟（120 * 15秒）

while [ $CHECK_COUNT -lt $MAX_CHECKS ]; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    
    echo "[检查 $CHECK_COUNT] $(date '+%H:%M:%S')"
    
    # 检查测试日志
    LATEST_LOG=$(ls -t "$LOG_DIR"/e2e_test_*.log 2>/dev/null | head -1)
    
    if [ -n "$LATEST_LOG" ]; then
        # 检查是否完成
        if tail -100 "$LATEST_LOG" | grep -qiE "测试.*完成|所有.*完成|测试执行完成|所有任务完成"; then
            echo ""
            echo "========================================"
            echo "测试已完成！"
            echo "========================================"
            echo ""
            
            # 显示最后的结果
            echo "最终日志:"
            echo "----------------------------------------"
            tail -30 "$LATEST_LOG"
            echo "----------------------------------------"
            echo ""
            
            # 检查是否成功
            if tail -100 "$LATEST_LOG" | grep -qiE "所有测试通过|✅.*成功|测试.*成功"; then
                echo "✅ 所有任务成功完成！"
                exit 0
            elif tail -100 "$LATEST_LOG" | grep -qiE "测试失败|❌.*失败"; then
                echo "❌ 测试失败"
                echo ""
                echo "错误信息:"
                grep -iE "error|失败|错误|failed" "$LATEST_LOG" | tail -10
                exit 1
            else
                echo "⚠️  测试已完成，状态未知"
                exit 0
            fi
        else
            # 显示进度
            LAST_LINE=$(tail -1 "$LATEST_LOG" 2>/dev/null | cut -c1-80)
            echo "  进度: ${LAST_LINE}"
        fi
    else
        echo "  等待日志文件..."
    fi
    
    # 检查进程是否还在运行
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo ""
            echo "测试进程已结束，检查最终结果..."
            if [ -n "$LATEST_LOG" ]; then
                echo ""
                echo "最终日志:"
                tail -50 "$LATEST_LOG"
            fi
            break
        fi
    fi
    
    echo ""
    sleep 15
done

if [ $CHECK_COUNT -ge $MAX_CHECKS ]; then
    echo ""
    echo "⚠️  达到最大检查次数，监控结束"
    echo "请手动查看日志: $LATEST_LOG"
fi
