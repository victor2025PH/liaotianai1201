#!/bin/bash
# 修復端口 3000 被佔用問題

echo "=========================================="
echo "檢查並修復端口 3000 佔用問題"
echo "=========================================="

# 檢查端口 3000 是否被佔用
echo ""
echo "=== 檢查端口 3000 狀態 ==="

# 使用 ss 命令
if command -v ss > /dev/null; then
    PORT_INFO=$(ss -tlnp | grep :3000 || true)
    if [ -n "$PORT_INFO" ]; then
        echo "⚠️  端口 3000 已被佔用:"
        echo "$PORT_INFO"
        echo ""
        
        # 提取進程ID
        PID=$(ss -tlnp | grep :3000 | grep -oP 'pid=\K[0-9]+' | head -1)
        if [ -n "$PID" ]; then
            echo "找到佔用端口的進程:"
            ps aux | grep $PID | grep -v grep
            echo ""
            echo "正在終止進程 $PID..."
            kill $PID
            sleep 2
            
            # 如果還在運行，強制終止
            if ps -p $PID > /dev/null 2>&1; then
                echo "進程仍在運行，強制終止..."
                kill -9 $PID
                sleep 1
            fi
            
            echo "✅ 進程已終止"
        fi
    else
        echo "✅ 端口 3000 可用"
    fi
else
    # 使用 lsof 作為備選
    if command -v lsof > /dev/null; then
        PID=$(lsof -ti :3000 || true)
        if [ -n "$PID" ]; then
            echo "⚠️  端口 3000 被進程 $PID 佔用"
            ps aux | grep $PID | grep -v grep
            echo ""
            echo "正在終止進程..."
            kill $PID
            sleep 2
            echo "✅ 進程已終止"
        else
            echo "✅ 端口 3000 可用"
        fi
    else
        echo "⚠️  無法檢查端口（需要安裝 ss 或 lsof）"
        echo "   安裝命令: sudo apt install -y net-tools lsof"
    fi
fi

echo ""
echo "=== 清理舊的前端進程 ==="
# 查找所有 next.js 相關進程
NEXT_PIDS=$(ps aux | grep -E "node.*next|next.*start" | grep -v grep | awk '{print $2}' || true)
if [ -n "$NEXT_PIDS" ]; then
    echo "找到舊的前端進程: $NEXT_PIDS"
    echo "$NEXT_PIDS" | xargs kill 2>/dev/null || true
    sleep 2
    echo "✅ 已清理舊進程"
else
    echo "✅ 沒有舊的前端進程"
fi

echo ""
echo "=========================================="
echo "✅ 端口檢查完成"
echo "=========================================="
