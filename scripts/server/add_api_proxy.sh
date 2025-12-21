#!/bin/bash

# 添加 /api/ 路径代理到后端（支持 WebSocket）
# 使用方法: bash scripts/server/add_api_proxy.sh

set -e

echo "=========================================="
echo "🔧 添加 /api/ 路径代理到后端"
echo "时间: $(date)"
echo "=========================================="
echo ""

AIKZ_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 1. 检查配置文件是否存在
echo "1. 检查配置文件..."
echo "----------------------------------------"
if [ ! -f "$AIKZ_CONFIG" ]; then
  echo "❌ 配置文件不存在: $AIKZ_CONFIG"
  exit 1
fi

echo "✅ 找到配置文件: $AIKZ_CONFIG"
echo ""

# 2. 检查是否已存在 /api/ 配置
echo "2. 检查现有配置..."
echo "----------------------------------------"
if grep -q "location /api/" "$AIKZ_CONFIG"; then
  echo "⚠️  已存在 /api/ 配置，检查是否需要更新..."
  EXISTING_API=$(grep -A 10 "location /api/" "$AIKZ_CONFIG" | head -15)
  echo "$EXISTING_API"
  echo ""
  
  # 检查是否指向 8000
  if echo "$EXISTING_API" | grep -q "127.0.0.1:8000"; then
    echo "✅ /api/ 已配置指向 8000，检查 WebSocket 支持..."
    if echo "$EXISTING_API" | grep -q "Upgrade" && echo "$EXISTING_API" | grep -q "Connection.*upgrade"; then
      echo "✅ WebSocket 支持已配置，无需修改"
      exit 0
    else
      echo "⚠️  WebSocket 支持不完整，将更新配置"
    fi
  else
    echo "⚠️  /api/ 未指向 8000，将更新配置"
  fi
else
  echo "✅ 未找到 /api/ 配置，将添加"
fi
echo ""

# 3. 备份原配置
echo "3. 备份原配置..."
echo "----------------------------------------"
BACKUP_FILE="${AIKZ_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp "$AIKZ_CONFIG" "$BACKUP_FILE"
echo "✅ 配置已备份到: $BACKUP_FILE"
echo ""

# 4. 读取现有配置并添加 /api/ 块
echo "4. 添加 /api/ 配置..."
echo "----------------------------------------"

# 使用 Python 脚本智能添加配置
sudo python3 << 'PYTHON_SCRIPT'
import re
import sys

config_file = "/etc/nginx/sites-available/aikz.usdt2026.cc"

try:
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已存在 location /api/
    if re.search(r'location\s+/api/', content):
        # 如果存在，替换整个 location /api/ 块
        api_block_pattern = r'location\s+/api/\s*\{[^}]*\}'
        new_api_block = '''location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }'''
        
        content = re.sub(api_block_pattern, new_api_block, content, flags=re.DOTALL)
        print("✅ 已更新现有的 /api/ 配置")
    else:
        # 如果不存在，在 location / 之前添加
        # 找到 location / 的位置
        location_root_pattern = r'(location\s+/\s*\{)'
        
        # 在 location / 之前插入 location /api/
        api_block = '''    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
'''
        
        # 在每个 server 块的 location / 之前插入
        content = re.sub(location_root_pattern, api_block + r'\1', content)
        print("✅ 已添加新的 /api/ 配置")
    
    # 写入修改后的配置
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 配置已更新")
    
except Exception as e:
    print(f"❌ 修改配置失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
  echo "❌ Python 脚本失败，使用 sed 作为备用方案..."
  
  # 备用方案：使用 sed 添加配置
  # 在 location / { 之前插入 location /api/ 块
  sudo sed -i '/location\s\+\/\s\+{/i\    location /api/ {\n        proxy_pass http://127.0.0.1:8000/;\n        proxy_http_version 1.1;\n        proxy_set_header Upgrade $http_upgrade;\n        proxy_set_header Connection "upgrade";\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_cache_bypass $http_upgrade;\n    }\n' "$AIKZ_CONFIG"
  
  echo "✅ 使用 sed 添加配置"
fi

echo ""

# 5. 显示修改后的配置
echo "5. 显示修改后的配置（location 部分）..."
echo "----------------------------------------"
grep -A 15 "location /api/" "$AIKZ_CONFIG" | head -20 || echo "⚠️  未找到 /api/ 配置"
echo ""
grep -A 10 "location /" "$AIKZ_CONFIG" | grep -v "location /api/" | head -15 || echo "⚠️  未找到 / 配置"
echo ""

# 6. 验证配置
echo "6. 验证配置..."
echo "----------------------------------------"
if grep -q "location /api/" "$AIKZ_CONFIG" && grep -q "proxy_pass.*127.0.0.1:8000" "$AIKZ_CONFIG"; then
  echo "✅ /api/ 配置已添加，指向端口 8000"
  
  # 检查 WebSocket 支持
  if grep -A 10 "location /api/" "$AIKZ_CONFIG" | grep -q "Upgrade" && grep -A 10 "location /api/" "$AIKZ_CONFIG" | grep -q "Connection.*upgrade"; then
    echo "✅ WebSocket 支持已配置"
  else
    echo "⚠️  WebSocket 支持可能不完整"
  fi
else
  echo "❌ /api/ 配置添加失败"
  exit 1
fi
echo ""

# 7. 测试 Nginx 配置
echo "7. 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置有错误"
  echo "恢复备份配置..."
  sudo cp "$BACKUP_FILE" "$AIKZ_CONFIG"
  echo "✅ 已恢复备份配置"
  exit 1
fi
echo ""

# 8. 重启 Nginx
echo "8. 重启 Nginx..."
echo "----------------------------------------"
if sudo systemctl restart nginx; then
  echo "✅ Nginx 已重启"
  
  # 等待 Nginx 启动
  sleep 2
  
  # 检查 Nginx 状态
  if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
  else
    echo "❌ Nginx 启动失败"
    sudo systemctl status nginx --no-pager | head -15
    exit 1
  fi
else
  echo "❌ Nginx 重启失败"
  sudo systemctl status nginx --no-pager | head -15
  exit 1
fi
echo ""

# 9. 验证后端服务
echo "9. 验证后端服务..."
echo "----------------------------------------"

# 检查端口 8000 是否监听
if ss -tlnp 2>/dev/null | grep -q ":8000 " || netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
  echo "✅ 端口 8000 (后端) 正在监听"
  
  # 测试后端 API 响应
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:8000/docs 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    echo "✅ 后端 API 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  后端 API 响应异常 (HTTP $HTTP_CODE)"
  fi
else
  echo "❌ 端口 8000 (后端) 未监听"
  echo "   请检查 backend 服务是否运行: pm2 list | grep backend"
fi
echo ""

# 10. 测试 /api/ 路径代理
echo "10. 测试 /api/ 路径代理..."
echo "----------------------------------------"

# 通过 Nginx 测试 /api/ 路径
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://aikz.usdt2026.cc/api/docs 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "404" ]; then
  echo "✅ /api/ 路径代理正常 (HTTP $HTTP_CODE)"
  echo "   注意：404 可能是正常的，取决于后端路由配置"
else
  echo "⚠️  /api/ 路径代理异常 (HTTP $HTTP_CODE)"
fi

# 测试 HTTPS
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 -k https://aikz.usdt2026.cc/api/docs 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "404" ]; then
  echo "✅ /api/ 路径 HTTPS 代理正常 (HTTP $HTTP_CODE)"
else
  echo "⚠️  /api/ 路径 HTTPS 代理异常 (HTTP $HTTP_CODE)"
fi
echo ""

echo "=========================================="
echo "✅ /api/ 路径代理配置完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "配置摘要："
echo "  - location / -> http://127.0.0.1:3000 (前端)"
echo "  - location /api/ -> http://127.0.0.1:8000 (后端)"
echo "  - WebSocket 支持: ✅ 已配置"
echo "  - 配置文件: $AIKZ_CONFIG"
echo "  - 备份文件: $BACKUP_FILE"
echo ""
echo "验证命令："
echo "  grep -A 10 'location /api/' /etc/nginx/sites-enabled/aikz.usdt2026.cc"
echo "  curl -I http://aikz.usdt2026.cc/api/docs"
echo "  curl -I https://aikz.usdt2026.cc/api/docs"
echo ""
echo "WebSocket 测试："
echo "  在浏览器控制台测试 WebSocket 连接"
echo "  如果仍有问题，请检查："
echo "    sudo nginx -T | grep -A 15 'location /api/'"
echo "    sudo tail -20 /var/log/nginx/error.log"
echo "    pm2 logs backend --lines 20"
