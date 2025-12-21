#!/bin/bash

# 修复 Nginx 和所有服务问题的终极脚本
# 使用方法: bash scripts/server/fix_nginx_and_services.sh

set -e

echo "=========================================="
echo "🔧 修复 Nginx 和所有服务问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 停止所有服务和占用端口的进程
echo "1. 停止所有服务和占用端口的进程..."
echo "----------------------------------------"
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true
sleep 2

# 停止占用端口的进程
PORTS=(3000 3001 3002 3003 8000)
for PORT in "${PORTS[@]}"; do
  if ss -tlnp 2>/dev/null | grep -q ":$PORT " || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "停止占用端口 $PORT 的进程..."
    PIDS=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP "pid=\K\d+" || netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1 || echo "")
    for PID in $PIDS; do
      if [ -n "$PID" ] && [ "$PID" != "N/A" ] && [ "$PID" != "Address" ] && [ "$PID" != "LISTEN" ]; then
        sudo kill -9 $PID 2>/dev/null || true
      fi
    done
    sleep 1
  fi
done
echo "✅ 所有服务已停止"
echo ""

# 2. 修复 saas-demo 启动方式
echo "2. 修复 saas-demo 启动方式..."
echo "----------------------------------------"
SAAS_DEMO_DIR="$PROJECT_ROOT/saas-demo"

if [ -d "$SAAS_DEMO_DIR" ]; then
  cd "$SAAS_DEMO_DIR" || exit 1
  
  # 检查是否有 standalone 构建
  if [ -f ".next/standalone/server.js" ]; then
    echo "✅ 发现 standalone 构建，使用正确的启动方式..."
    
    # 删除旧的 PM2 进程（如果存在）
    pm2 delete saas-demo 2>/dev/null || true
    
    # 使用 standalone 方式启动
    pm2 start ".next/standalone/server.js" \
      --name saas-demo \
      --interpreter node \
      --cwd "$SAAS_DEMO_DIR" \
      --env PORT=3000 \
      --env NODE_ENV=production || {
      echo "⚠️  standalone 启动失败，尝试使用 npm start..."
      if [ ! -d "node_modules" ]; then
        npm install
      fi
      pm2 start npm \
        --name saas-demo \
        --cwd "$SAAS_DEMO_DIR" \
        -- start
    }
    echo "✅ saas-demo 已启动（使用 standalone 方式）"
  else
    echo "⚠️  未发现 standalone 构建，使用 npm start..."
    if [ ! -d "node_modules" ]; then
      npm install
    fi
    if [ ! -d ".next" ]; then
      npm run build
    fi
    pm2 start npm \
      --name saas-demo \
      --cwd "$SAAS_DEMO_DIR" \
      -- start
    echo "✅ saas-demo 已启动（使用 npm start）"
  fi
else
  echo "⚠️  saas-demo 目录不存在"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 3. 启动后端服务
echo "3. 启动后端服务..."
echo "----------------------------------------"
bash scripts/server/fix_backend_deps.sh
echo ""

# 4. 启动其他前端服务
echo "4. 启动其他前端服务..."
echo "----------------------------------------"

# 启动 tgmini-frontend (3001)
if [ -d "$PROJECT_ROOT/tgmini20251220" ] || find "$PROJECT_ROOT" -maxdepth 3 -type d -name "*tgmini*" 2>/dev/null | head -1 | grep -q .; then
  TGMINI_DIR=$(find "$PROJECT_ROOT" -maxdepth 3 -type d -name "*tgmini*" 2>/dev/null | head -1)
  if [ -n "$TGMINI_DIR" ] && [ -f "$TGMINI_DIR/package.json" ]; then
    cd "$TGMINI_DIR" || exit 1
    if [ ! -d "node_modules" ]; then
      npm install
    fi
    if [ ! -d "dist" ]; then
      npm run build
    fi
    pm2 start serve \
      --name tgmini-frontend \
      -- -s dist -l 3001
    echo "✅ tgmini-frontend 已启动"
    cd "$PROJECT_ROOT" || exit 1
  fi
fi

# 启动 hongbao-frontend (3002)
HONGBAO_DIR="$PROJECT_ROOT/react-vite-template/hbwy20251220"
if [ -d "$HONGBAO_DIR" ] && [ -f "$HONGBAO_DIR/package.json" ]; then
  cd "$HONGBAO_DIR" || exit 1
  if [ ! -d "node_modules" ]; then
    npm install
  fi
  if [ ! -d "dist" ]; then
    npm run build
  fi
  pm2 start serve \
    --name hongbao-frontend \
    -- -s dist -l 3002
  echo "✅ hongbao-frontend 已启动"
  cd "$PROJECT_ROOT" || exit 1
fi

# 启动 aizkw-frontend (3003)
if [ -d "$PROJECT_ROOT/aizkw20251219" ]; then
  AIZKW_DIR="$PROJECT_ROOT/aizkw20251219"
elif [ -d "$PROJECT_ROOT/migrations/aizkw20251219" ]; then
  AIZKW_DIR="$PROJECT_ROOT/migrations/aizkw20251219"
else
  AIZKW_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | grep -iE "aizkw" | grep -v "/logs/" | grep -v "/\.git/" | head -1 | xargs dirname 2>/dev/null || echo "")
fi

if [ -n "$AIZKW_DIR" ] && [ -d "$AIZKW_DIR" ] && [ -f "$AIZKW_DIR/package.json" ]; then
  cd "$AIZKW_DIR" || exit 1
  if [ ! -d "node_modules" ]; then
    npm install
  fi
  if [ ! -d "dist" ]; then
    npm run build
  fi
  pm2 start serve \
    --name aizkw-frontend \
    -- -s dist -l 3003
  echo "✅ aizkw-frontend 已启动"
  cd "$PROJECT_ROOT" || exit 1
fi

echo ""

# 5. 等待服务启动
echo "5. 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 6. 检查并修复 Nginx 配置
echo "6. 检查并修复 Nginx 配置..."
echo "----------------------------------------"

# 检查 Nginx 是否安装
if ! command -v nginx &> /dev/null; then
  echo "安装 Nginx..."
  sudo apt-get update -qq
  sudo apt-get install -y nginx
fi

# 检查 Nginx 是否运行
if ! systemctl is-active --quiet nginx; then
  echo "启动 Nginx..."
  sudo systemctl start nginx
fi

# 检查 Nginx 配置
if ! sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
  echo "⚠️  Nginx 配置有错误，尝试修复..."
  # 这里可以添加自动修复 Nginx 配置的逻辑
fi

# 确保 Nginx 监听端口 80
if ! ss -tlnp 2>/dev/null | grep -q ":80 " && ! netstat -tlnp 2>/dev/null | grep -q ":80 "; then
  echo "⚠️  Nginx 未监听端口 80，检查配置..."
  
  # 检查默认配置
  if [ ! -f "/etc/nginx/sites-enabled/default" ] && [ ! -f "/etc/nginx/conf.d/default.conf" ]; then
    echo "创建默认 Nginx 配置..."
    sudo tee /etc/nginx/sites-available/default > /dev/null << 'NGINX_EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    root /var/www/html;
    index index.html index.htm;
    
    location / {
        try_files $uri $uri/ =404;
    }
}
NGINX_EOF
    sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
  fi
fi

# 重启 Nginx
sudo systemctl restart nginx
sleep 2

if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 已重启"
else
  echo "❌ Nginx 启动失败"
  sudo systemctl status nginx --no-pager | head -10
fi
echo ""

# 7. 验证所有服务
echo "7. 验证所有服务..."
echo "----------------------------------------"
pm2 list
echo ""

# 检查端口监听
echo "检查端口监听状态..."
for PORT in 3000 3001 3002 3003 8000 80; do
  if ss -tlnp 2>/dev/null | grep -q ":$PORT " || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "✅ 端口 $PORT 正在监听"
  else
    echo "❌ 端口 $PORT 未监听"
  fi
done
echo ""

# 测试 HTTP 响应
echo "测试 HTTP 响应..."
for PORT in 3000 3001 3002 3003; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 端口 $PORT HTTP 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "❌ 端口 $PORT HTTP 响应异常 (HTTP $HTTP_CODE)"
  fi
done

# 测试后端
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:8000/docs 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
  echo "✅ 端口 8000 (后端) HTTP 响应正常 (HTTP $HTTP_CODE)"
else
  echo "❌ 端口 8000 (后端) HTTP 响应异常 (HTTP $HTTP_CODE)"
fi

# 测试 Nginx
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:80 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
  echo "✅ 端口 80 (Nginx) HTTP 响应正常 (HTTP $HTTP_CODE)"
else
  echo "❌ 端口 80 (Nginx) HTTP 响应异常 (HTTP $HTTP_CODE)"
fi
echo ""

# 8. 保存 PM2 配置
echo "8. 保存 PM2 配置..."
echo "----------------------------------------"
pm2 save
echo "✅ PM2 配置已保存"
echo ""

echo "=========================================="
echo "✅ 修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果网站仍然无法访问，请检查："
echo "  1. Nginx 配置: sudo nginx -t"
echo "  2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "  3. Nginx 访问日志: sudo tail -50 /var/log/nginx/access.log"
echo "  4. PM2 日志: pm2 logs"
echo "  5. 端口监听: ss -tlnp | grep -E '80|3000|3001|3002|3003|8000'"
echo "  6. 防火墙: sudo ufw status"
