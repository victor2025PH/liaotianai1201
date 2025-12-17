#!/bin/bash
# 自動處理 git pull 時的本地更改問題

echo "=========================================="
echo "處理 Git 本地更改並拉取最新代碼"
echo "=========================================="
echo ""

cd /home/ubuntu/telegram-ai-system || exit 1

# 檢查是否有未提交的更改
echo "[1/3] 檢查本地更改..."
echo "----------------------------------------"
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️  發現未提交的更改："
  git status --short
  echo ""
  echo "選擇處理方式："
  echo "  1. 暫存本地更改（推薦，可以稍後恢復）"
  echo "  2. 丟棄本地更改（使用遠程版本）"
  echo "  3. 取消操作"
  echo ""
  
  # 自動選擇：如果有修改的是我們創建的腳本文件，丟棄本地更改
  CHANGED_FILES=$(git status --porcelain | awk '{print $2}')
  if echo "$CHANGED_FILES" | grep -q "scripts/server/"; then
    echo "檢測到腳本文件更改，自動丟棄本地更改以使用遠程版本..."
    git checkout -- .
    echo "✅ 本地更改已丟棄"
  else
    echo "暫存本地更改..."
    git stash push -m "Auto-stash before pull $(date +%Y%m%d_%H%M%S)"
    echo "✅ 本地更改已暫存"
  fi
else
  echo "✅ 沒有未提交的更改"
fi
echo ""

# 拉取最新代碼
echo "[2/3] 拉取最新代碼..."
echo "----------------------------------------"
git pull origin main
if [ $? -eq 0 ]; then
  echo "✅ 代碼已更新"
  git log --oneline -1
else
  echo "❌ 拉取代碼失敗"
  exit 1
fi
echo ""

# 更新腳本權限
echo "[3/3] 更新腳本權限..."
echo "----------------------------------------"
chmod +x scripts/server/*.sh 2>/dev/null || true
echo "✅ 完成"
echo ""

echo "=========================================="
echo "準備完成！"
echo "=========================================="
