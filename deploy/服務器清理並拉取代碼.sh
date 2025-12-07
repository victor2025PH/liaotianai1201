#!/bin/bash
# 清理服務器本地變更並拉取最新代碼

set -e

echo "=========================================="
echo "清理本地變更並拉取最新代碼"
echo "=========================================="

cd ~/liaotian || {
    echo "❌ 無法進入項目目錄"
    exit 1
}

# 1. 查看當前狀態
echo ""
echo "=== 1. 當前 Git 狀態 ==="
git status

# 2. 處理未追蹤的文件
echo ""
echo "=== 2. 處理未追蹤文件 ==="
# 備份未追蹤的文件（如果需要）
if [ -f "admin-backend/start_auto_redpacket.py" ]; then
    echo "備份 start_auto_redpacket.py"
    mv admin-backend/start_auto_redpacket.py admin-backend/start_auto_redpacket.py.bak 2>/dev/null || true
fi

if [ -f "admin-backend/worker_auto_redpacket.py" ]; then
    echo "備份 worker_auto_redpacket.py"
    mv admin-backend/worker_auto_redpacket.py admin-backend/worker_auto_redpacket.py.bak 2>/dev/null || true
fi

# 3. 處理本地修改的文件
echo ""
echo "=== 3. 處理本地修改 ==="
# 選項 A：暫存變更（保留但暫時移除）
echo "暫存本地變更..."
git stash save "本地變更備份 $(date +%Y%m%d_%H%M%S)" || {
    # 如果暫存失敗，提交變更
    echo "暫存失敗，嘗試提交..."
    git add deploy/从GitHub拉取并部署.sh 2>/dev/null || true
    git commit -m "保存本地修改 $(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
}

# 4. 拉取最新代碼
echo ""
echo "=== 4. 拉取最新代碼 ==="
git fetch origin
git pull origin main || git pull origin master

# 5. 恢復暫存的變更（如果需要）
echo ""
echo "=== 5. 檢查暫存的變更 ==="
if git stash list | grep -q .; then
    echo "有暫存的變更，可以執行以下命令恢復："
    echo "  git stash pop"
    echo "或者查看暫存列表："
    echo "  git stash list"
fi

echo ""
echo "=========================================="
echo "✅ 代碼更新完成"
echo "=========================================="
