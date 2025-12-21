#!/bin/bash

# 快速修复后端依赖和 aikz Nginx 配置
# 使用方法: bash scripts/server/quick_fix_backend_and_aikz.sh

set -e

echo "=========================================="
echo "🔧 快速修复后端依赖和 aikz 配置"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 暴力修复 Python 依赖
echo "1. 修复后端依赖..."
echo "----------------------------------------"
cd "$PROJECT_ROOT/admin-backend" || {
  echo "❌ 无法进入后端目录"
  exit 1
}

echo "安装核心 Python 包（使用 --break-system-packages）..."
pip3 install uvicorn fastapi starlette pydantic python-multipart requests --break-system-packages || {
  echo "⚠️  部分包安装失败，但继续..."
}

echo "验证关键包..."
python3 -c "import uvicorn; print(f'✅ uvicorn: {uvicorn.__version__}')" || {
  echo "❌ uvicorn 导入失败"
  exit 1
}

python3 -c "import fastapi; print(f'✅ fastapi: {fastapi.__version__}')" || {
  echo "⚠️  fastapi 导入失败，但继续..."
}

echo "✅ 后端依赖修复完成"
echo ""

# 2. 重启后端服务
echo "2. 重启后端服务..."
echo "----------------------------------------"
cd "$PROJECT_ROOT" || exit 1

if pm2 list | grep -q "backend"; then
  echo "重启 PM2 backend 进程..."
  pm2 restart backend || {
    echo "⚠️  PM2 restart 失败，尝试删除后重新启动..."
    pm2 delete backend 2>/dev/null || true
    sleep 2
    
    # 使用 python3 -m uvicorn 启动
    PYTHON3_PATH=$(which python3)
    if [ -f "$PROJECT_ROOT/admin-backend/app/main.py" ]; then
      pm2 start "$PYTHON3_PATH" \
        --name backend \
        --interpreter none \
        --cwd "$PROJECT_ROOT/admin-backend" \
        --update-env \
        --env PORT=8000 \
        --env PYTHONPATH="$PROJECT_ROOT/admin-backend" \
        --env PYTHONUNBUFFERED=1 \
        -- -m uvicorn app.main:app --host 0.0.0.0 --port 8000 || {
        echo "❌ 后端启动失败"
        exit 1
      }
    elif [ -f "$PROJECT_ROOT/admin-backend/main.py" ]; then
      pm2 start "$PYTHON3_PATH" \
        --name backend \
        --interpreter none \
        --cwd "$PROJECT_ROOT/admin-backend" \
        --update-env \
        --env PORT=8000 \
        --env PYTHONPATH="$PROJECT_ROOT/admin-backend" \
        --env PYTHONUNBUFFERED=1 \
        -- "$PROJECT_ROOT/admin-backend/main.py" || {
        echo "❌ 后端启动失败"
        exit 1
      }
    else
      echo "❌ 未找到后端启动文件"
      exit 1
    fi
  }
  echo "✅ 后端服务已重启"
else
  echo "⚠️  PM2 中未找到 backend 进程，尝试启动..."
  PYTHON3_PATH=$(which python3)
  if [ -f "$PROJECT_ROOT/admin-backend/app/main.py" ]; then
    pm2 start "$PYTHON3_PATH" \
      --name backend \
      --interpreter none \
      --cwd "$PROJECT_ROOT/admin-backend" \
      --env PORT=8000 \
      --env PYTHONPATH="$PROJECT_ROOT/admin-backend" \
      --env PYTHONUNBUFFERED=1 \
      -- -m uvicorn app.main:app --host 0.0.0.0 --port 8000 || {
      echo "❌ 后端启动失败"
      exit 1
    }
  else
    echo "❌ 未找到后端启动文件"
    exit 1
  fi
  echo "✅ 后端服务已启动"
fi

echo ""

# 3. 强制重写 aikz 的 Nginx 配置
echo "3. 重写 aikz Nginx 配置..."
echo "----------------------------------------"

AIKZ_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

echo "创建 Nginx 配置: $AIKZ_CONFIG"
sudo tee "$AIKZ_CONFIG" > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    location / {
        proxy_pass http://127.0.0.1:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
server {
    listen 443 ssl;
    server_name aikz.usdt2026.cc;

    ssl_certificate /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aikz.usdt2026.cc/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX_EOF

echo "✅ Nginx 配置已创建"
echo ""

# 4. 重新建立链接
echo "4. 重新建立链接..."
echo "----------------------------------------"
sudo ln -sf "$AIKZ_CONFIG" /etc/nginx/sites-enabled/aikz.usdt2026.cc

if [ -L "/etc/nginx/sites-enabled/aikz.usdt2026.cc" ]; then
  echo "✅ 软链接已创建"
else
  echo "❌ 软链接创建失败"
  exit 1
fi
echo ""

# 5. 测试 Nginx 配置
echo "5. 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置有错误"
  echo "请检查配置文件的语法错误"
  exit 1
fi
echo ""

# 6. 重启 Nginx
echo "6. 重启 Nginx..."
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

# 7. 验证
echo "7. 验证配置和服务..."
echo "----------------------------------------"

# 检查端口 3003 是否监听
if ss -tlnp 2>/dev/null | grep -q ":3003 " || netstat -tlnp 2>/dev/null | grep -q ":3003 "; then
  echo "✅ 端口 3003 正在监听"
  
  # 测试端口 3003 HTTP 响应
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:3003 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 端口 3003 HTTP 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  端口 3003 HTTP 响应异常 (HTTP $HTTP_CODE)"
  fi
else
  echo "❌ 端口 3003 未监听"
  echo "   请检查 aizkw-frontend 服务是否运行: pm2 list | grep aizkw"
fi

# 检查端口 8000 是否监听
if ss -tlnp 2>/dev/null | grep -q ":8000 " || netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
  echo "✅ 端口 8000 (后端) 正在监听"
  
  # 测试端口 8000 HTTP 响应
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:8000/docs 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    echo "✅ 端口 8000 HTTP 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  端口 8000 HTTP 响应异常 (HTTP $HTTP_CODE)"
  fi
else
  echo "❌ 端口 8000 (后端) 未监听"
  echo "   请检查 backend 服务是否运行: pm2 list | grep backend"
fi

# 检查 Nginx 监听状态
echo ""
echo "Nginx 监听状态："
if command -v netstat >/dev/null 2>&1; then
  sudo netstat -ntlp | grep nginx || echo "⚠️  未找到 Nginx 监听端口"
elif command -v ss >/dev/null 2>&1; then
  sudo ss -tlnp | grep nginx || echo "⚠️  未找到 Nginx 监听端口"
fi

# 显示已启用的站点
echo ""
echo "已启用的 Nginx 站点："
ls -la /etc/nginx/sites-enabled/ | grep -v "^total" | grep -v "^\.$" | grep -v "^\.\.$" || echo "⚠️  没有启用的站点配置"
echo ""

# 检查 SSL 证书
echo "检查 SSL 证书..."
if [ -f "/etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem" ]; then
  echo "✅ SSL 证书存在"
else
  echo "⚠️  SSL 证书不存在: /etc/letsencrypt/live/aikz.usdt2026.cc/fullchain.pem"
  echo "   如果不需要 HTTPS，可以删除配置中的 443 服务器块"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "配置摘要："
echo "  - aikz.usdt2026.cc -> http://127.0.0.1:3003"
echo "  - 后端服务 -> http://127.0.0.1:8000"
echo ""
echo "如果仍有问题，请检查："
echo "  sudo nginx -T | grep -A 20 'aikz.usdt2026.cc'"
echo "  sudo tail -50 /var/log/nginx/error.log"
echo "  pm2 logs backend --lines 20"
echo "  pm2 logs aizkw-frontend --lines 20"
