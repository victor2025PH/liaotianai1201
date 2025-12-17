#!/bin/bash
# 簡單修復 Nginx 靜態文件配置

echo "=========================================="
echo "簡單修復 Nginx 靜態文件配置"
echo "=========================================="
echo ""

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 備份配置
sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

# 確定正確的路徑
if [ -d "/home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static" ]; then
  STATIC_PATH="/home/ubuntu/telegram-ai-system/saas-demo/.next/standalone/.next/static/"
  echo "使用 standalone 目錄: $STATIC_PATH"
elif [ -d "/home/ubuntu/telegram-ai-system/saas-demo/.next/static" ]; then
  STATIC_PATH="/home/ubuntu/telegram-ai-system/saas-demo/.next/static/"
  echo "使用標準目錄: $STATIC_PATH"
else
  echo "❌ 找不到靜態文件目錄"
  exit 1
fi

# 移除舊的配置（如果存在 try_files 或 fallback）
echo ""
echo "清理舊配置..."
sudo sed -i '/@next_static_fallback/d' "$NGINX_CONFIG"
sudo sed -i '/try_files.*@next_static_fallback/d' "$NGINX_CONFIG"

# 更新或添加配置
echo "更新配置..."
sudo python3 << PYTHON_SCRIPT
import re

config_file = '/etc/nginx/sites-available/aikz.usdt2026.cc'
static_path = '${STATIC_PATH}'

with open(config_file, 'r') as f:
    content = f.read()

# 新的配置塊（簡化版，不使用 try_files）
new_location = f'''    # Next.js 靜態文件 - 直接從文件系統提供（優先級最高）
    location /next/static/ {{
        alias {static_path};
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }}

'''

# 檢查是否已存在 location /next/static/
if 'location /next/static/' in content:
    # 替換現有配置
    pattern = r'location /next/static/.*?access_log off;\s*\}'
    content = re.sub(pattern, new_location.rstrip(), content, flags=re.DOTALL)
    
    # 確保 alias 路徑正確
    content = re.sub(
        r'(location /next/static/\s*\{[^}]*alias\s+)([^;]+)(;)',
        r'\1' + static_path + r'\3',
        content,
        flags=re.DOTALL
    )
    
    print("✅ 配置已更新")
else:
    # 在 location /api/v1/notifications/ws 之後添加
    pattern = r'(location /api/v1/notifications/ws \{.*?\n    \})\n'
    replacement = r'\1\n' + new_location
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print("✅ 配置已添加")

with open(config_file, 'w') as f:
    f.write(content)
PYTHON_SCRIPT

# 修復文件權限
echo ""
echo "修復文件權限..."
sudo chown -R ubuntu:ubuntu /home/ubuntu/telegram-ai-system/saas-demo/.next
sudo chmod -R 755 /home/ubuntu/telegram-ai-system/saas-demo/.next

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
  echo "恢復備份..."
  sudo cp "${NGINX_CONFIG}.backup."* "$NGINX_CONFIG" 2>/dev/null || true
  exit 1
fi

echo ""
echo "=========================================="
echo "修復完成！"
echo "=========================================="
echo ""
echo "當前配置："
sudo grep -A 3 "location /next/static/" "$NGINX_CONFIG"
echo ""
echo "請清除瀏覽器緩存並重新訪問網站測試"
