#!/bin/bash
# 部署紅包 SDK 更新到服務器
# 執行時間：2025-12-03

echo "=========================================="
echo "  部署紅包 SDK 更新"
echo "=========================================="
echo ""

# 進入項目目錄
cd ~/liaotian || exit 1

# 1. 拉取最新代碼
echo "[1/4] 拉取最新代碼..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "❌ Git pull 失敗"
    exit 1
fi
echo "✅ 代碼拉取成功"
echo ""

# 2. 重啟後端服務
echo "[2/4] 重啟後端服務..."
cd admin-backend
sudo systemctl restart liaotian-backend
sleep 2
if sudo systemctl is-active --quiet liaotian-backend; then
    echo "✅ 後端服務重啟成功"
else
    echo "⚠️  後端服務狀態異常，請檢查日誌: sudo journalctl -u liaotian-backend -n 50"
fi
echo ""

# 3. 重建前端
echo "[3/4] 重建前端..."
cd ../saas-demo
npm run build
if [ $? -ne 0 ]; then
    echo "❌ 前端構建失敗"
    exit 1
fi
echo "✅ 前端構建成功"
echo ""

# 4. 重啟前端服務
echo "[4/4] 重啟前端服務..."
sudo systemctl restart liaotian-frontend
sleep 2
if sudo systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服務重啟成功"
else
    echo "⚠️  前端服務狀態異常，請檢查日誌: sudo journalctl -u liaotian-frontend -n 50"
fi
echo ""

# 5. 檢查服務狀態
echo "=========================================="
echo "  服務狀態檢查"
echo "=========================================="
echo ""
echo "後端服務:"
sudo systemctl status liaotian-backend --no-pager -l | head -5
echo ""
echo "前端服務:"
sudo systemctl status liaotian-frontend --no-pager -l | head -5
echo ""

echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 訪問 https://aikz.usdt2026.cc/group-ai/redpacket 配置紅包 API"
echo "2. 重新下載 Worker 部署包（包含紅包 SDK 支持）"
echo "3. 在 Worker 中設置環境變量或使用 Excel 配置"
echo ""
