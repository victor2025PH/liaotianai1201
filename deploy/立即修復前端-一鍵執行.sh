#!/bin/bash
# 立即修復前端問題 - 一鍵執行
# 解決：1. TypeScript 錯誤 2. standalone 模式啟動命令 3. 缺少構建文件

set -e  # 遇到錯誤立即退出

echo "=========================================="
echo "  立即修復前端部署問題"
echo "=========================================="
echo ""

cd ~/liaotian || { echo "❌ 無法進入項目目錄"; exit 1; }

# 步驟 1: 拉取最新代碼
echo "[1/5] 拉取最新代碼..."
git pull origin main
echo "✅ 完成"
echo ""

# 步驟 2: 修復 systemd 服務配置
echo "[2/5] 修復 systemd 服務配置..."
SERVICE_FILE="/etc/systemd/system/liaotian-frontend.service"
WORK_DIR="/home/ubuntu/liaotian/saas-demo"

# 備份原文件
if [ -f "$SERVICE_FILE" ]; then
    sudo cp "$SERVICE_FILE" "${SERVICE_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
fi

# 創建正確的服務文件
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Liaotian AI Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$WORK_DIR
Environment="NODE_ENV=production"
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/node $WORK_DIR/.next/standalone/server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo "✅ 服務配置已更新（使用 standalone 模式）"
echo ""

# 步驟 3: 進入前端目錄並安裝依賴
echo "[3/5] 檢查依賴..."
cd saas-demo
if [ ! -d "node_modules" ]; then
    echo "安裝依賴..."
    npm install
fi
echo "✅ 完成"
echo ""

# 步驟 4: 清理並重新構建
echo "[4/5] 清理舊構建並重新構建..."
rm -rf .next
npm run build

# 檢查構建是否成功
if [ ! -f ".next/standalone/server.js" ]; then
    echo "❌ 構建失敗：找不到 standalone/server.js"
    echo "   請檢查構建錯誤信息"
    exit 1
fi
echo "✅ 構建成功"
echo ""

# 步驟 5: 設置權限並重啟服務
echo "[5/5] 設置權限並重啟服務..."
sudo chown -R ubuntu:ubuntu .next
sudo systemctl restart liaotian-frontend

# 等待服務啟動
sleep 5

# 檢查服務狀態
if sudo systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 服務啟動成功"
else
    echo "⚠️  服務啟動失敗，查看日誌："
    sudo journalctl -u liaotian-frontend -n 30 --no-pager
    exit 1
fi
echo ""

# 顯示最終狀態
echo "=========================================="
echo "  ✅ 修復完成！"
echo "=========================================="
echo ""
echo "服務狀態："
sudo systemctl status liaotian-frontend --no-pager | head -10
echo ""
echo "最新日誌："
sudo journalctl -u liaotian-frontend -n 5 --no-pager
echo ""
