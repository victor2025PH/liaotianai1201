#!/bin/bash
# 修復前端部署問題
# 1. 修復 TypeScript 錯誤
# 2. 修復 systemd 服務配置（standalone 模式）

echo "=========================================="
echo "  修復前端部署問題"
echo "=========================================="
echo ""

# 進入項目目錄
cd ~/liaotian || exit 1

# 步驟 1: 拉取最新代碼（確保 TypeScript 修復已包含）
echo "[1/4] 拉取最新代碼..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "❌ Git pull 失敗"
    exit 1
fi
echo "✅ 代碼拉取成功"
echo ""

# 步驟 2: 檢查並修復 systemd 服務配置
echo "[2/4] 檢查 systemd 服務配置..."
SERVICE_FILE="/etc/systemd/system/liaotian-frontend.service"

if [ -f "$SERVICE_FILE" ]; then
    echo "找到服務文件: $SERVICE_FILE"
    
    # 檢查是否使用正確的啟動命令
    if grep -q "next start" "$SERVICE_FILE"; then
        echo "⚠️  檢測到使用 'next start'，需要修復為 standalone 模式"
        
        # 備份原文件
        sudo cp "$SERVICE_FILE" "${SERVICE_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
        
        # 獲取工作目錄
        WORK_DIR=$(grep "WorkingDirectory=" "$SERVICE_FILE" | cut -d'=' -f2)
        if [ -z "$WORK_DIR" ]; then
            WORK_DIR="/home/ubuntu/liaotian/saas-demo"
        fi
        
        # 創建新的服務文件
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
        
        echo "✅ 服務文件已更新"
        echo "   新啟動命令: node $WORK_DIR/.next/standalone/server.js"
        
        # 重新加載 systemd
        sudo systemctl daemon-reload
        echo "✅ systemd 已重新加載"
    else
        echo "✅ 服務配置看起來正確"
    fi
else
    echo "⚠️  服務文件不存在: $SERVICE_FILE"
    echo "   創建新的服務文件..."
    
    WORK_DIR="/home/ubuntu/liaotian/saas-demo"
    
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
    sudo systemctl enable liaotian-frontend
    echo "✅ 新服務文件已創建並啟用"
fi
echo ""

# 步驟 3: 重新構建前端
echo "[3/4] 重新構建前端..."
cd saas-demo

# 確保依賴已安裝
if [ ! -d "node_modules" ]; then
    echo "安裝依賴..."
    npm install
fi

# 構建
npm run build
if [ $? -ne 0 ]; then
    echo "❌ 前端構建失敗"
    echo "   請檢查錯誤信息並修復 TypeScript 錯誤"
    exit 1
fi
echo "✅ 前端構建成功"
echo ""

# 步驟 4: 重啟服務
echo "[4/4] 重啟前端服務..."
sudo systemctl restart liaotian-frontend
sleep 3

if sudo systemctl is-active --quiet liaotian-frontend; then
    echo "✅ 前端服務啟動成功"
else
    echo "⚠️  前端服務啟動失敗，查看日誌:"
    sudo journalctl -u liaotian-frontend -n 20 --no-pager
    exit 1
fi
echo ""

# 顯示服務狀態
echo "=========================================="
echo "  服務狀態"
echo "=========================================="
sudo systemctl status liaotian-frontend --no-pager | head -15
echo ""

echo "=========================================="
echo "  ✅ 修復完成！"
echo "=========================================="
echo ""
echo "驗證步驟:"
echo "1. 檢查服務狀態: sudo systemctl status liaotian-frontend"
echo "2. 查看日誌: sudo journalctl -u liaotian-frontend -f"
echo "3. 訪問網站: https://aikz.usdt2026.cc"
echo ""
