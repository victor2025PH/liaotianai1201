#!/bin/bash

# 检查 aikz.usdt2026.cc 的问题
# 使用方法: bash scripts/server/check_aikz_issue.sh

set -e

echo "=========================================="
echo "🔍 检查 aikz.usdt2026.cc 问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"
NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN"

# 1. 检查 Nginx 配置
echo "1. 检查 Nginx 配置..."
echo "----------------------------------------"
if [ -f "$NGINX_CONFIG" ]; then
  echo "✅ 配置文件存在: $NGINX_CONFIG"
  echo ""
  echo "配置内容（proxy_pass 部分）："
  grep -A 5 "proxy_pass" "$NGINX_CONFIG" | head -10
  echo ""
  
  # 检查指向的端口
  PROXY_PORT=$(grep "proxy_pass" "$NGINX_CONFIG" | grep -oP "127\.0\.0\.1:\K\d+" | head -1)
  if [ -n "$PROXY_PORT" ]; then
    echo "当前配置指向端口: $PROXY_PORT"
    if [ "$PROXY_PORT" = "3000" ]; then
      echo "✅ 配置正确（指向 saas-demo）"
    else
      echo "❌ 配置错误！应该指向端口 3000，但当前指向 $PROXY_PORT"
    fi
  fi
else
  echo "❌ 配置文件不存在: $NGINX_CONFIG"
fi

if [ -L "$NGINX_ENABLED" ]; then
  echo "✅ 符号链接存在: $NGINX_ENABLED"
  echo "   指向: $(readlink -f $NGINX_ENABLED)"
else
  echo "❌ 符号链接不存在: $NGINX_ENABLED"
fi
echo ""

# 2. 检查是否有多个配置
echo "2. 检查是否有重复配置..."
echo "----------------------------------------"
DUPLICATE_COUNT=$(sudo grep -r "server_name $DOMAIN" /etc/nginx/sites-enabled/ 2>/dev/null | wc -l || echo "0")
if [ "$DUPLICATE_COUNT" -gt 1 ]; then
  echo "⚠️  发现多个配置（可能冲突）:"
  sudo grep -r "server_name $DOMAIN" /etc/nginx/sites-enabled/ 2>/dev/null
else
  echo "✅ 没有重复配置"
fi
echo ""

# 3. 检查 saas-demo 服务
echo "3. 检查 saas-demo 服务..."
echo "----------------------------------------"
if lsof -i :3000 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":3000 "; then
  echo "✅ 端口 3000 正在监听"
  PROCESS_INFO=$(lsof -i :3000 2>/dev/null | grep LISTEN | head -1 || ss -tlnp 2>/dev/null | grep ":3000 " | head -1)
  echo "   进程信息: $PROCESS_INFO"
  
  # 测试本地访问
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 本地访问正常 (HTTP $HTTP_CODE)"
    
    # 检查返回的内容
    echo ""
    echo "检查返回的内容（前 500 字符）："
    CONTENT=$(curl -s http://127.0.0.1:3000 2>/dev/null | head -c 500)
    echo "$CONTENT"
    echo ""
    
    # 检查是否包含 "AI 智控王"（错误的页面）
    if echo "$CONTENT" | grep -qi "智控王\|Smart Control King"; then
      echo "❌ 返回的内容包含 'AI 智控王'，说明返回了错误的页面"
      echo "   这可能是 saas-demo 构建问题，或者返回了其他项目的页面"
    else
      echo "✅ 返回的内容不包含 'AI 智控王'"
    fi
    
    # 检查是否包含 "登录" 或 "login"（正确的页面）
    if echo "$CONTENT" | grep -qi "登录\|login\|聊天 AI"; then
      echo "✅ 返回的内容包含登录相关文字，可能是正确的页面"
    else
      echo "⚠️  返回的内容不包含登录相关文字"
    fi
  else
    echo "⚠️  本地访问异常 (HTTP $HTTP_CODE)"
  fi
else
  echo "❌ 端口 3000 未监听"
fi
echo ""

# 4. 检查 PM2 进程
echo "4. 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  SAAS_DEMO_STATUS=$(pm2 list | grep saas-demo || echo "")
  if [ -n "$SAAS_DEMO_STATUS" ]; then
    echo "PM2 进程状态:"
    echo "$SAAS_DEMO_STATUS"
    
    if echo "$SAAS_DEMO_STATUS" | grep -q "errored\|stopped"; then
      echo "❌ saas-demo 进程状态异常"
      echo "查看日志："
      pm2 logs saas-demo --lines 20 --nostream 2>/dev/null || true
    else
      echo "✅ saas-demo 进程运行中"
    fi
  else
    echo "❌ 未找到 saas-demo PM2 进程"
  fi
else
  echo "⚠️  PM2 未安装"
fi
echo ""

# 5. 检查 saas-demo 构建
echo "5. 检查 saas-demo 构建..."
echo "----------------------------------------"
SAAS_DEMO_DIR="/home/ubuntu/telegram-ai-system/saas-demo"
if [ -d "$SAAS_DEMO_DIR" ]; then
  echo "✅ saas-demo 目录存在"
  
  if [ -d "$SAAS_DEMO_DIR/.next" ]; then
    echo "✅ .next 目录存在（已构建）"
    NEXT_SIZE=$(du -sh "$SAAS_DEMO_DIR/.next" 2>/dev/null | cut -f1)
    echo "   大小: $NEXT_SIZE"
  else
    echo "❌ .next 目录不存在（未构建）"
  fi
  
  if [ -f "$SAAS_DEMO_DIR/package.json" ]; then
    echo "✅ package.json 存在"
  else
    echo "❌ package.json 不存在"
  fi
else
  echo "❌ saas-demo 目录不存在"
fi
echo ""

# 6. 测试外部访问
echo "6. 测试外部访问..."
echo "----------------------------------------"
EXTERNAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN 2>/dev/null || echo "000")
if [ "$EXTERNAL_CODE" = "200" ]; then
  echo "✅ 外部访问正常 (HTTP $EXTERNAL_CODE)"
  
  # 检查返回的内容
  EXTERNAL_CONTENT=$(curl -s https://$DOMAIN 2>/dev/null | head -c 500)
  echo ""
  echo "返回的内容（前 500 字符）："
  echo "$EXTERNAL_CONTENT"
  echo ""
  
  # 检查是否包含 "AI 智控王"
  if echo "$EXTERNAL_CONTENT" | grep -qi "智控王\|Smart Control King"; then
    echo "❌ 外部访问返回的内容包含 'AI 智控王'，说明返回了错误的页面"
  else
    echo "✅ 外部访问返回的内容不包含 'AI 智控王'"
  fi
else
  echo "⚠️  外部访问异常 (HTTP $EXTERNAL_CODE)"
fi
echo ""

# 7. 检查是否有其他服务占用
echo "7. 检查端口占用情况..."
echo "----------------------------------------"
echo "端口 3000:"
lsof -i :3000 2>/dev/null || ss -tlnp 2>/dev/null | grep ":3000 " || echo "未监听"
echo ""
echo "端口 3003:"
lsof -i :3003 2>/dev/null || ss -tlnp 2>/dev/null | grep ":3003 " || echo "未监听"
echo ""

echo "=========================================="
echo "📊 诊断总结"
echo "=========================================="
echo ""
echo "如果 Nginx 配置指向错误的端口："
echo "  运行: sudo bash scripts/server/fix_aikz_nginx.sh"
echo ""
echo "如果 saas-demo 未构建："
echo "  cd /home/ubuntu/telegram-ai-system/saas-demo"
echo "  npm install"
echo "  npm run build"
echo "  pm2 restart saas-demo"
echo ""
echo "如果返回了错误的页面内容："
echo "  可能是浏览器缓存，尝试强制刷新 (Ctrl+F5)"
echo "  或者检查 saas-demo 的构建输出是否正确"
