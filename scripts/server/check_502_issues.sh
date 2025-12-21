#!/bin/bash

echo "=========================================="
echo "🔍 诊断 502 错误问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 检查前端服务端口
echo "1️⃣ 检查前端服务端口监听..."
echo "----------------------------------------"
for port in 3001 3002 3003; do
  PORT_STATUS=$(sudo netstat -tlnp 2>/dev/null | grep ":$port " || sudo ss -tlnp 2>/dev/null | grep ":$port " || echo "")
  if [ -n "$PORT_STATUS" ]; then
    echo "✅ 端口 $port 正在监听"
    echo "   $PORT_STATUS"
  else
    echo "❌ 端口 $port 未监听"
  fi
done
echo ""

# 检查 PM2 进程
echo "2️⃣ 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  pm2 list
  echo ""
  
  # 检查每个前端服务
  for name in "tgmini-frontend" "hongbao-frontend" "aizkw-frontend"; do
    if pm2 list | grep -q "$name"; then
      STATUS=$(pm2 jlist | jq -r ".[] | select(.name==\"$name\") | .pm2_env.status" 2>/dev/null || pm2 describe "$name" 2>/dev/null | grep "status" | awk '{print $4}')
      echo "✅ $name: $STATUS"
    else
      echo "❌ $name: 未运行"
    fi
  done
else
  echo "⚠️  PM2 未安装"
fi
echo ""

# 测试本地端口连接
echo "3️⃣ 测试本地端口连接..."
echo "----------------------------------------"
for port in 3001 3002 3003; do
  echo "测试端口 $port..."
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://127.0.0.1:$port 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "  ✅ 端口 $port 响应正常 (HTTP $HTTP_CODE)"
  elif [ "$HTTP_CODE" = "000" ]; then
    echo "  ❌ 端口 $port 无法连接（服务未运行）"
  else
    echo "  ⚠️  端口 $port 响应异常 (HTTP $HTTP_CODE)"
  fi
done
echo ""

# 检查 Nginx 配置
echo "4️⃣ 检查 Nginx 配置..."
echo "----------------------------------------"
DOMAINS=("tgmini.usdt2026.cc" "hongbao.usdt2026.cc" "aikz.usdt2026.cc" "aizkw.usdt2026.cc")
for domain in "${DOMAINS[@]}"; do
  CONFIG_FILE="/etc/nginx/sites-enabled/$domain"
  if [ -f "$CONFIG_FILE" ] || [ -L "$CONFIG_FILE" ]; then
    echo "✅ $domain: 配置存在"
    
    # 检查代理端口
    PROXY_PORT=$(grep "proxy_pass.*127.0.0.1" "$CONFIG_FILE" 2>/dev/null | grep -oP ":\K\d+" | head -1 || echo "")
    if [ -n "$PROXY_PORT" ]; then
      echo "   代理端口: $PROXY_PORT"
      
      # 检查端口是否监听
      PORT_LISTENING=$(sudo netstat -tlnp 2>/dev/null | grep ":$PROXY_PORT " || echo "")
      if [ -n "$PORT_LISTENING" ]; then
        echo "   ✅ 端口 $PROXY_PORT 正在监听"
      else
        echo "   ❌ 端口 $PROXY_PORT 未监听（这会导致 502）"
      fi
    fi
  else
    echo "❌ $domain: 配置不存在"
  fi
done
echo ""

# 测试 HTTPS 访问
echo "5️⃣ 测试 HTTPS 访问..."
echo "----------------------------------------"
for domain in "${DOMAINS[@]}"; do
  echo "测试 $domain..."
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 https://$domain 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "  ✅ $domain 响应正常 (HTTP $HTTP_CODE)"
  elif [ "$HTTP_CODE" = "502" ]; then
    echo "  ❌ $domain 返回 502 Bad Gateway"
    echo "     原因: Nginx 无法连接到后端服务"
  elif [ "$HTTP_CODE" = "000" ]; then
    echo "  ❌ $domain 无法连接"
  else
    echo "  ⚠️  $domain 响应异常 (HTTP $HTTP_CODE)"
  fi
done
echo ""

# 检查 package.json 文件
echo "6️⃣ 检查 package.json 文件..."
echo "----------------------------------------"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
SITES=(
  "tgmini20251220:3001"
  "hbwy20251220:3002"
  "aizkw20251219:3003"
)

for site_info in "${SITES[@]}"; do
  IFS=':' read -r dir port <<< "$site_info"
  SITE_DIR="$PROJECT_DIR/$dir"
  PACKAGE_JSON="$SITE_DIR/package.json"
  
  echo "项目: $dir (端口 $port)"
  if [ -f "$PACKAGE_JSON" ]; then
    echo "  ✅ package.json 存在"
  else
    echo "  ❌ package.json 不存在"
    echo "     需要从本地上传文件到: $SITE_DIR"
  fi
done
echo ""

echo "=========================================="
echo "✅ 诊断完成"
echo "时间: $(date)"
echo "=========================================="
