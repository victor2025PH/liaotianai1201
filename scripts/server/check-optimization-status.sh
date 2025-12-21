#!/bin/bash
# 检查优化代码是否已部署

echo "=== 优化代码部署状态检查 ==="
echo ""

cd ~/telegram-ai-system || exit 1

# 1. 检查 Git 状态
echo "1. 检查 Git 状态..."
echo "   当前分支: $(git branch --show-current)"
echo "   未推送提交数: $(git rev-list --count origin/main..HEAD 2>/dev/null || echo '未知')"
echo "   未提交修改:"
git status --short | head -5
echo ""

# 2. 检查前端轮询优化
echo "2. 检查前端轮询优化..."
FRONTEND_DIR="saas-demo/src"

# 检查关键文件
check_files=(
    "hooks/useRealtimeMetrics.ts:10000"
    "hooks/useSystemMonitor.ts:10000"
    "hooks/useMetrics.ts:10000"
    "hooks/useDashboardData.ts:30000"
    "components/layout-wrapper.tsx:30000"
)

for file_check in "${check_files[@]}"; do
    file="${file_check%%:*}"
    expected="${file_check##*:}"
    file_path="$FRONTEND_DIR/$file"
    
    if [ -f "$file_path" ]; then
        # 检查是否包含优化后的值
        if grep -q "$expected" "$file_path" 2>/dev/null; then
            echo "   ✅ $file: 已优化为 ${expected}ms"
        elif grep -qE "(refetchInterval|setInterval).*[0-9]+" "$file_path" 2>/dev/null; then
            actual=$(grep -oE "(refetchInterval|setInterval).*[0-9]+" "$file_path" | head -1 | grep -oE "[0-9]+" | head -1)
            echo "   ⚠️  $file: 当前为 ${actual}ms（期望: ${expected}ms）"
        else
            echo "   ❓ $file: 无法确定状态"
        fi
    else
        echo "   ❌ $file: 文件不存在"
    fi
done
echo ""

# 3. 检查后端心跳优化
echo "3. 检查后端心跳优化..."
BACKEND_FILE="admin-backend/app/api/workers.py"

if [ -f "$BACKEND_FILE" ]; then
    if grep -q "ACCOUNT_SYNC_INTERVAL" "$BACKEND_FILE"; then
        interval=$(grep "ACCOUNT_SYNC_INTERVAL" "$BACKEND_FILE" | grep -oE "[0-9]+" | head -1)
        echo "   ✅ 账号同步间隔: 每 $interval 次心跳"
    else
        echo "   ❌ 未找到 ACCOUNT_SYNC_INTERVAL（优化可能未应用）"
    fi
    
    if grep -q "_account_sync_counters" "$BACKEND_FILE"; then
        echo "   ✅ 已使用同步计数器"
    else
        echo "   ❌ 未找到同步计数器（优化可能未应用）"
    fi
    
    if grep -q "sync_in_background\|threading" "$BACKEND_FILE"; then
        echo "   ✅ 已使用后台线程同步"
    else
        echo "   ⚠️  可能未使用后台线程同步"
    fi
else
    echo "   ❌ 后端文件不存在"
fi
echo ""

# 4. 检查系统监控脚本
echo "4. 检查系统监控脚本频率..."
if crontab -u ubuntu -l 2>/dev/null | grep -q "monitor-system.sh"; then
    cron_line=$(crontab -u ubuntu -l 2>/dev/null | grep "monitor-system.sh")
    if echo "$cron_line" | grep -q "\*/10"; then
        echo "   ✅ Crontab 已优化为每 10 分钟"
    elif echo "$cron_line" | grep -q "\*/5"; then
        echo "   ⚠️  Crontab 仍为每 5 分钟（应优化为每 10 分钟）"
    else
        echo "   ❓ Crontab 频率: $cron_line"
    fi
else
    echo "   ❌ 未找到 monitor-system.sh 的 Crontab 配置"
fi
echo ""

# 5. 检查服务运行状态
echo "5. 检查服务运行状态..."
pm2 list | grep -E "backend|frontend" | head -2
echo ""

# 6. 检查最近的重启时间
echo "6. 检查服务运行时间..."
BACKEND_UPTIME=$(pm2 list | grep backend | awk '{print $10}' | head -1)
FRONTEND_UPTIME=$(pm2 list | grep frontend | awk '{print $10}' | head -1)
echo "   后端运行时间: $BACKEND_UPTIME"
echo "   前端运行时间: $FRONTEND_UPTIME"
echo ""

# 7. 总结
echo "=== 检查完成 ==="
echo ""
echo "如果发现优化未应用，请执行："
echo "  1. git pull origin main  # 拉取最新代码"
echo "  2. cd saas-demo && npm run build  # 重新构建前端"
echo "  3. pm2 restart all  # 重启服务"
