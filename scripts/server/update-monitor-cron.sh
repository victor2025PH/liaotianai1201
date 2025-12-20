#!/bin/bash

# 更新系統監控腳本的 Crontab 頻率
# 從每分鐘或每 5 分鐘改為每 10 分鐘執行一次

set -e

MONITOR_SCRIPT="/home/ubuntu/telegram-ai-system/scripts/server/monitor-system.sh"

echo "=========================================="
echo "更新系統監控 Crontab 頻率"
echo "=========================================="

# 檢查監控腳本是否存在
if [ ! -f "$MONITOR_SCRIPT" ]; then
    echo "⚠️  警告: 監控腳本不存在: $MONITOR_SCRIPT"
    echo "請確認腳本路徑是否正確"
    exit 1
fi

# 備份當前 crontab
echo "📋 備份當前 crontab..."
BACKUP_FILE="/tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
crontab -u ubuntu -l > "$BACKUP_FILE" 2>/dev/null || echo "# 空 crontab" > "$BACKUP_FILE"
echo "✅ 備份已保存到: $BACKUP_FILE"

# 移除舊的 monitor-system.sh 任務（無論頻率如何）
echo "🗑️  移除舊的監控任務..."
(crontab -u ubuntu -l 2>/dev/null | grep -v "monitor-system.sh" || true) > /tmp/crontab_new.txt

# 添加新的任務（每 10 分鐘執行一次）
echo "➕ 添加新的監控任務（每 10 分鐘執行一次）..."
echo "*/10 * * * * $MONITOR_SCRIPT >> /home/ubuntu/telegram-ai-system/logs/monitor.log 2>&1" >> /tmp/crontab_new.txt

# 安裝新的 crontab
crontab -u ubuntu /tmp/crontab_new.txt
rm /tmp/crontab_new.txt

echo "✅ Crontab 已更新"
echo ""
echo "新的監控頻率: 每 10 分鐘執行一次 (*/10 * * * *)"
echo ""
echo "驗證新的 crontab:"
crontab -u ubuntu -l | grep "monitor-system.sh" || echo "未找到 monitor-system.sh 任務"

echo ""
echo "=========================================="
echo "✅ 更新完成！"
echo "=========================================="
