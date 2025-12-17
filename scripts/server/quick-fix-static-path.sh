#!/bin/bash
# 快速修復 Nginx 靜態文件路徑

echo "=========================================="
echo "快速修復 Nginx 靜態文件路徑"
echo "=========================================="
echo ""

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 檢查 standalone 目錄是否存在
if [ -d "/home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static" ]; then
  NEW_PATH="/home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static/"
  echo "✅ 找到 standalone 靜態文件目錄"
  echo "   將使用路徑: $NEW_PATH"
elif [ -d "/home/ubuntu/telegram-ai-system/saas-demo/.next/static" ]; then
  NEW_PATH="/home/ubuntu/telegram-ai-system/saas-demo/.next/static/"
  echo "⚠️  使用標準靜態文件目錄"
  echo "   將使用路徑: $NEW_PATH"
else
  echo "❌ 找不到靜態文件目錄"
  exit 1
fi

# 更新 Nginx 配置
echo ""
echo "更新 Nginx 配置..."
sudo sed -i "s|alias /home/ubuntu/telegram-ai-system/saas-demo/.next/static/|alias $NEW_PATH|g" "$NGINX_CONFIG"
sudo sed -i "s|alias /home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static/|alias $NEW_PATH|g" "$NGINX_CONFIG"

# 驗證更新
if sudo grep -q "alias $NEW_PATH" "$NGINX_CONFIG"; then
  echo "✅ 配置已更新"
else
  echo "⚠️  自動更新失敗，需要手動檢查"
fi

# 測試配置
echo ""
echo "測試 Nginx 配置..."
if sudo nginx -t; then
  echo "✅ 配置語法正確"
  echo "重載 Nginx..."
  sudo systemctl reload nginx
  echo "✅ Nginx 已重載"
else
  echo "❌ 配置語法錯誤"
  exit 1
fi

echo ""
echo "=========================================="
echo "修復完成！"
echo "=========================================="
echo ""
echo "當前配置的靜態文件路徑："
sudo grep "alias.*static" "$NGINX_CONFIG" | head -1
echo ""
echo "請清除瀏覽器緩存並重新訪問網站測試"
