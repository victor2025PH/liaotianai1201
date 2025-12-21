#!/bin/bash

# 修复 /api/ 路径代理配置（去掉尾部斜杠以保留 /api/ 前缀）
# 使用方法: bash scripts/server/fix_api_proxy_path.sh

set -e

echo "=========================================="
echo "🔧 修复 /api/ 路径代理配置"
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

# 2. 显示当前配置
echo "2. 当前 /api/ 配置..."
echo "----------------------------------------"
grep -A 10 "location /api/" "$AIKZ_CONFIG" | head -15 || echo "⚠️  未找到 /api/ 配置"
echo ""

# 3. 备份原配置
echo "3. 备份原配置..."
echo "----------------------------------------"
BACKUP_FILE="${AIKZ_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp "$AIKZ_CONFIG" "$BACKUP_FILE"
echo "✅ 配置已备份到: $BACKUP_FILE"
echo ""

# 4. 修复配置：去掉 proxy_pass 的尾部斜杠
echo "4. 修复配置（去掉 proxy_pass 尾部斜杠）..."
echo "----------------------------------------"

# 检查是否有尾部斜杠
if grep -q "location /api/" "$AIKZ_CONFIG" && grep -A 2 "location /api/" "$AIKZ_CONFIG" | grep -q "proxy_pass.*8000/;"; then
  echo "发现 proxy_pass 有尾部斜杠，将修复..."
  
  # 替换 proxy_pass http://127.0.0.1:8000/; 为 proxy_pass http://127.0.0.1:8000;
  sudo sed -i 's|proxy_pass http://127.0.0.1:8000/;|proxy_pass http://127.0.0.1:8000;|g' "$AIKZ_CONFIG"
  
  echo "✅ 已去掉尾部斜杠"
else
  echo "⚠️  未找到需要修复的配置，或配置已经是正确的"
  
  # 检查当前配置
  if grep -A 2 "location /api/" "$AIKZ_CONFIG" | grep -q "proxy_pass.*8000;"; then
    echo "✅ 配置已经是正确的（没有尾部斜杠）"
  else
    echo "❌ 配置可能有问题，请检查"
  fi
fi
echo ""

# 5. 显示修改后的配置
echo "5. 修改后的 /api/ 配置..."
echo "----------------------------------------"
grep -A 10 "location /api/" "$AIKZ_CONFIG" | head -15 || echo "⚠️  未找到 /api/ 配置"
echo ""

# 6. 验证配置
echo "6. 验证配置..."
echo "----------------------------------------"
if grep -A 2 "location /api/" "$AIKZ_CONFIG" | grep -q "proxy_pass.*http://127.0.0.1:8000;"; then
  echo "✅ 配置已修复：proxy_pass 指向 http://127.0.0.1:8000（无尾部斜杠）"
  echo "   这样会保留 /api/ 前缀，请求 /api/v1/auth/login 会被转发为 /api/v1/auth/login"
else
  echo "❌ 配置修复失败"
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

# 9. 测试登录 API
echo "9. 测试登录 API..."
echo "----------------------------------------"

# 测试 /api/v1/auth/login 端点
echo "测试 POST /api/v1/auth/login..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 -X POST http://aikz.usdt2026.cc/api/v1/auth/login -d "username=test&password=test" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "401" ]; then
  echo "✅ /api/v1/auth/login 端点可访问 (HTTP $HTTP_CODE)"
  echo "   注意：422 或 401 是正常的，表示端点存在但参数验证失败"
elif [ "$HTTP_CODE" = "404" ]; then
  echo "❌ /api/v1/auth/login 端点返回 404，路径可能仍然不正确"
  echo "   请检查后端路由配置"
else
  echo "⚠️  /api/v1/auth/login 端点响应异常 (HTTP $HTTP_CODE)"
fi

# 测试 HTTPS
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 -k -X POST https://aikz.usdt2026.cc/api/v1/auth/login -d "username=test&password=test" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "401" ]; then
  echo "✅ /api/v1/auth/login HTTPS 端点可访问 (HTTP $HTTP_CODE)"
else
  echo "⚠️  /api/v1/auth/login HTTPS 端点响应异常 (HTTP $HTTP_CODE)"
fi
echo ""

# 10. 显示配置说明
echo "10. 配置说明..."
echo "----------------------------------------"
echo "修复说明："
echo "  - 之前: proxy_pass http://127.0.0.1:8000/; (有尾部斜杠)"
echo "    -> 请求 /api/v1/auth/login 被转发为 /v1/auth/login (去掉了 /api/)"
echo ""
echo "  - 现在: proxy_pass http://127.0.0.1:8000; (无尾部斜杠)"
echo "    -> 请求 /api/v1/auth/login 被转发为 /api/v1/auth/login (保留了 /api/)"
echo ""
echo "这样后端就能正确匹配路由了！"
echo ""

echo "=========================================="
echo "✅ /api/ 路径代理配置修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "配置摘要："
echo "  - location /api/ -> http://127.0.0.1:8000 (无尾部斜杠，保留 /api/ 前缀)"
echo "  - 配置文件: $AIKZ_CONFIG"
echo "  - 备份文件: $BACKUP_FILE"
echo ""
echo "验证命令："
echo "  grep -A 5 'location /api/' /etc/nginx/sites-enabled/aikz.usdt2026.cc"
echo "  curl -X POST http://aikz.usdt2026.cc/api/v1/auth/login -d 'username=test&password=test'"
echo ""
echo "如果登录仍有问题，请检查："
echo "  1. 后端路由是否正确: pm2 logs backend --lines 30"
echo "  2. Nginx 错误日志: sudo tail -30 /var/log/nginx/error.log"
echo "  3. 后端 API 文档: curl http://127.0.0.1:8000/docs"
