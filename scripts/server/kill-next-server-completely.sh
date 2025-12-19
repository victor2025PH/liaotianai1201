#!/bin/bash
# ============================================================
# 彻底杀掉 next-server 进程及其父进程
# ============================================================

echo "=========================================="
echo "🔪 彻底杀掉 next-server 进程"
echo "=========================================="
echo ""

# 循环清理，直到端口完全释放
MAX_ATTEMPTS=10
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "[尝试 $ATTEMPT/$MAX_ATTEMPTS] 查找并杀掉 next-server 进程..."
    
    # 查找占用端口 3000 的进程
    NEXT_PID=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " | grep -oP 'pid=\K\d+' | head -1 || echo "")
    
    if [ -z "$NEXT_PID" ]; then
        echo "✅ 端口 3000 已释放"
        break
    fi
    
    echo "发现进程 PID: $NEXT_PID"
    
    # 获取进程详细信息
    PROCESS_INFO=$(ps -fp $NEXT_PID -o pid,ppid,user,comm,args 2>/dev/null || echo "")
    if [ -n "$PROCESS_INFO" ]; then
        echo "进程信息:"
        echo "$PROCESS_INFO"
    fi
    
    # 获取父进程 ID
    PPID=$(ps -o ppid= -p $NEXT_PID 2>/dev/null | tr -d ' ' || echo "")
    if [ -n "$PPID" ] && [ "$PPID" != "1" ]; then
        echo "父进程 PID: $PPID"
        PARENT_INFO=$(ps -fp $PPID -o pid,ppid,user,comm,args 2>/dev/null || echo "")
        if [ -n "$PARENT_INFO" ]; then
            echo "父进程信息:"
            echo "$PARENT_INFO"
        fi
    fi
    
    # 杀掉进程及其父进程（如果不是 systemd）
    echo "杀掉进程 PID $NEXT_PID..."
    sudo kill -9 $NEXT_PID 2>/dev/null || true
    
    if [ -n "$PPID" ] && [ "$PPID" != "1" ]; then
        PARENT_COMM=$(ps -o comm= -p $PPID 2>/dev/null | tr -d ' ' || echo "")
        if [[ ! "$PARENT_COMM" =~ ^(systemd|init)$ ]]; then
            echo "杀掉父进程 PID $PPID..."
            sudo kill -9 $PPID 2>/dev/null || true
        fi
    fi
    
    # 使用其他方法清理
    sudo fuser -k -9 3000/tcp 2>/dev/null || true
    sudo pkill -9 -f "next-server" 2>/dev/null || true
    
    sleep 2
    
    # 检查是否还有进程
    REMAINING=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
    if [ -z "$REMAINING" ]; then
        echo "✅ 端口 3000 已释放"
        break
    else
        echo "⚠️  端口 3000 仍被占用，继续清理..."
        echo "$REMAINING"
    fi
done

# 最终验证
echo ""
echo "最终验证端口状态..."
FINAL_CHECK=$(sudo ss -tlnp 2>/dev/null | grep ":3000 " || echo "")
if [ -z "$FINAL_CHECK" ]; then
    echo "✅ 端口 3000 已完全释放"
    exit 0
else
    echo "❌ 端口 3000 仍被占用:"
    echo "$FINAL_CHECK"
    echo ""
    echo "占用进程的详细信息:"
    FINAL_PID=$(echo "$FINAL_CHECK" | grep -oP 'pid=\K\d+' | head -1 || echo "")
    if [ -n "$FINAL_PID" ]; then
        ps -fp $FINAL_PID -o pid,ppid,user,comm,args 2>/dev/null || true
        echo ""
        echo "进程树:"
        pstree -p $FINAL_PID 2>/dev/null || ps -ef | grep $FINAL_PID | grep -v grep || true
    fi
    exit 1
fi

