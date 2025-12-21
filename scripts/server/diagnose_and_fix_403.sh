#!/bin/bash

# 诊断和修复 403 Forbidden 问题
# 使用方法: bash scripts/server/diagnose_and_fix_403.sh

set -e

echo "=========================================="
echo "🔍 诊断和修复 403 Forbidden 问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 1. 检查 Nginx 配置
echo "1. 检查 Nginx 配置..."
echo "----------------------------------------"
sudo nginx -t
echo ""

# 2. 检查 Nginx 错误日志
echo "2. 检查 Nginx 错误日志（最近 20 行）..."
echo "----------------------------------------"
sudo tail -20 /var/log/nginx/error.log
echo ""

# 3. 检查 Nginx 访问日志
echo "3. 检查 Nginx 访问日志（最近 10 行）..."
echo "----------------------------------------"
sudo tail -10 /var/log/nginx/access.log
echo ""

# 4. 检查 Nginx 站点配置
echo "4. 检查 Nginx 站点配置..."
echo "----------------------------------------"
echo "已启用的站点："
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "⚠️  sites-enabled 目录不存在"
echo ""

# 5. 检查默认站点配置
echo "5. 检查默认站点配置..."
echo "----------------------------------------"
if [ -f "/etc/nginx/sites-enabled/default" ]; then
  echo "默认站点配置内容："
  cat /etc/nginx/sites-enabled/default | head -30
elif [ -f "/etc/nginx/conf.d/default.conf" ]; then
  echo "默认站点配置内容："
  cat /etc/nginx/conf.d/default.conf | head -30
else
  echo "⚠️  未找到默认站点配置"
  echo "创建默认站点配置..."
  
  sudo tee /etc/nginx/sites-available/default > /dev/null << 'NGINX_DEFAULT'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    # 根目录
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    
    # 日志
    access_log /var/log/nginx/default-access.log;
    error_log /var/log/nginx/default-error.log;
    
    # 代理到前端服务
    location / {
        # 尝试直接文件，否则代理到 saas-demo
        try_files $uri $uri/ @proxy;
    }
    
    location @proxy {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_DEFAULT
  
  sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
  echo "✅ 默认站点配置已创建"
fi
echo ""

# 6. 检查文件权限
echo "6. 检查文件权限..."
echo "----------------------------------------"
if [ -d "/var/www/html" ]; then
  echo "/var/www/html 权限："
  ls -ld /var/www/html
  sudo chown -R www-data:www-data /var/www/html 2>/dev/null || true
  sudo chmod -R 755 /var/www/html 2>/dev/null || true
  echo "✅ 文件权限已修复"
else
  echo "创建 /var/www/html 目录..."
  sudo mkdir -p /var/www/html
  sudo chown -R www-data:www-data /var/www/html
  sudo chmod -R 755 /var/www/html
  echo "✅ 目录已创建"
fi
echo ""

# 7. 检查后端服务
echo "7. 检查后端服务..."
echo "----------------------------------------"
if ss -tlnp 2>/dev/null | grep -q ":8000 " || netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
  echo "✅ 端口 8000 正在监听"
else
  echo "❌ 端口 8000 未监听，尝试修复后端..."
  bash scripts/server/fix_backend_deps.sh
fi
echo ""

# 8. 检查前端服务
echo "8. 检查前端服务..."
echo "----------------------------------------"
for PORT in 3000 3001 3002 3003; do
  if ss -tlnp 2>/dev/null | grep -q ":$PORT " || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$PORT 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
      echo "✅ 端口 $PORT 正常 (HTTP $HTTP_CODE)"
    else
      echo "⚠️  端口 $PORT 响应异常 (HTTP $HTTP_CODE)"
    fi
  else
    echo "❌ 端口 $PORT 未监听"
  fi
done
echo ""

# 9. 修复 hongbao-frontend 高 CPU 问题
echo "9. 修复 hongbao-frontend 高 CPU 问题..."
echo "----------------------------------------"
if pm2 list | grep -q "hongbao-frontend"; then
  CPU_USAGE=$(pm2 list | grep hongbao-frontend | awk '{print $10}' | grep -oE '[0-9]+' || echo "0")
  if [ "$CPU_USAGE" -gt 100 ]; then
    echo "⚠️  hongbao-frontend CPU 使用率过高: ${CPU_USAGE}%"
    echo "重启 hongbao-frontend..."
    pm2 restart hongbao-frontend
    sleep 5
    echo "✅ hongbao-frontend 已重启"
  else
    echo "✅ hongbao-frontend CPU 使用率正常"
  fi
fi
echo ""

# 10. 重新加载 Nginx 配置
echo "10. 重新加载 Nginx 配置..."
echo "----------------------------------------"
sudo nginx -t && sudo systemctl reload nginx
if [ $? -eq 0 ]; then
  echo "✅ Nginx 配置已重新加载"
else
  echo "❌ Nginx 配置重新加载失败"
  sudo systemctl status nginx --no-pager | head -10
fi
echo ""

# 11. 最终测试
echo "11. 最终测试..."
echo "----------------------------------------"
sleep 3

# 测试端口 80
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:80 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
  echo "✅ 端口 80 (Nginx) HTTP 响应正常 (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "403" ]; then
  echo "❌ 端口 80 仍然返回 403 Forbidden"
  echo "   请检查："
  echo "   1. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
  echo "   2. 文件权限: ls -la /var/www/html"
  echo "   3. Nginx 配置: sudo nginx -T | grep -A 20 'server {'"
else
  echo "⚠️  端口 80 HTTP 响应异常 (HTTP $HTTP_CODE)"
fi

# 测试端口 8000
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:8000/docs 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
  echo "✅ 端口 8000 (后端) HTTP 响应正常 (HTTP $HTTP_CODE)"
else
  echo "❌ 端口 8000 (后端) HTTP 响应异常 (HTTP $HTTP_CODE)"
fi
echo ""

echo "=========================================="
echo "诊断完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请执行以下命令查看详细信息："
echo "  sudo tail -50 /var/log/nginx/error.log"
echo "  sudo nginx -T"
echo "  pm2 logs backend --lines 30"
echo "  ss -tlnp | grep -E '80|8000'"
