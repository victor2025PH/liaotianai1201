#!/bin/bash
# 服務器端診斷和修復腳本拉取問題

set -e

echo "=========================================="
echo "診斷和修復腳本文件拉取問題"
echo "=========================================="

cd ~/liaotian || {
    echo "❌ 無法進入 ~/liaotian 目錄"
    exit 1
}

echo ""
echo "=== 1. 檢查 Git 狀態 ==="
git status
echo ""
git branch -a
echo ""

echo "=== 2. 檢查遠程倉庫配置 ==="
git remote -v
echo ""

echo "=== 3. 檢查文件是否在遠程倉庫中 ==="
echo "檢查 fix_and_deploy_frontend.sh:"
git ls-tree origin/main deploy/fix_and_deploy_frontend.sh 2>&1 || echo "未找到"
echo ""
echo "檢查 deploy_frontend_simple.sh:"
git ls-tree origin/main deploy/deploy_frontend_simple.sh 2>&1 || echo "未找到"
echo ""
echo "檢查 check_and_fix_frontend.sh:"
git ls-tree origin/main deploy/check_and_fix_frontend.sh 2>&1 || echo "未找到"
echo ""

echo "=== 4. 檢查本地文件 ==="
ls -la deploy/fix_and_deploy_frontend.sh 2>&1 || echo "本地不存在"
ls -la deploy/deploy_frontend_simple.sh 2>&1 || echo "本地不存在"
ls -la deploy/check_and_fix_frontend.sh 2>&1 || echo "本地不存在"
echo ""

echo "=== 5. 更新遠程引用 ==="
git fetch origin
git fetch origin main
echo ""

echo "=== 6. 切換到 main 分支 ==="
git checkout main 2>&1 || echo "已經在 main 分支"
echo ""

echo "=== 7. 拉取最新代碼 ==="
git pull origin main
echo ""

echo "=== 8. 強制從遠程獲取文件 ==="
git checkout origin/main -- deploy/fix_and_deploy_frontend.sh 2>&1 || {
    echo "嘗試直接從遠程獲取..."
    git show origin/main:deploy/fix_and_deploy_frontend.sh > deploy/fix_and_deploy_frontend.sh 2>&1 || echo "獲取失敗"
}

git checkout origin/main -- deploy/deploy_frontend_simple.sh 2>&1 || {
    echo "嘗試直接從遠程獲取..."
    git show origin/main:deploy/deploy_frontend_simple.sh > deploy/deploy_frontend_simple.sh 2>&1 || echo "獲取失敗"
}

git checkout origin/main -- deploy/check_and_fix_frontend.sh 2>&1 || {
    echo "嘗試直接從遠程獲取..."
    git show origin/main:deploy/check_and_fix_frontend.sh > deploy/check_and_fix_frontend.sh 2>&1 || echo "獲取失敗"
}

echo ""

echo "=== 9. 設置執行權限 ==="
chmod +x deploy/fix_and_deploy_frontend.sh 2>/dev/null || true
chmod +x deploy/deploy_frontend_simple.sh 2>/dev/null || true
chmod +x deploy/check_and_fix_frontend.sh 2>/dev/null || true

echo ""

echo "=== 10. 最終驗證 ==="
if [ -f "deploy/fix_and_deploy_frontend.sh" ]; then
    echo "✅ fix_and_deploy_frontend.sh 存在"
    ls -lh deploy/fix_and_deploy_frontend.sh
else
    echo "❌ fix_and_deploy_frontend.sh 不存在"
fi

if [ -f "deploy/deploy_frontend_simple.sh" ]; then
    echo "✅ deploy_frontend_simple.sh 存在"
    ls -lh deploy/deploy_frontend_simple.sh
else
    echo "❌ deploy_frontend_simple.sh 不存在"
fi

if [ -f "deploy/check_and_fix_frontend.sh" ]; then
    echo "✅ check_and_fix_frontend.sh 存在"
    ls -lh deploy/check_and_fix_frontend.sh
else
    echo "❌ check_and_fix_frontend.sh 不存在"
fi

echo ""
echo "=========================================="
echo "診斷完成"
echo "=========================================="
