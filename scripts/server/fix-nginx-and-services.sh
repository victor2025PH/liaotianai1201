#!/bin/bash
# ============================================================
# 修复 Nginx 和服务配置
# ============================================================

set -e

echo "=========================================="
echo "修复 Nginx 和服务配置"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# Step 1: 检查后端服务
echo ""
echo "[1/5] 检查后端服务..."
echo "----------------------------------------"
BACKEND_SERVICE="luckyred-api"
if systemctl is-active "$BACKEND_SERVICE" >/dev/null 2>&1; then
  echo "✅ 后端服务正在运行"
  BACKEND_STATUS="running"
else
  echo "⚠️  后端服务未运行，启动中..."
  sudo systemctl start "$BACKEND_SERVICE" || {
    echo "❌ 后端服务启动失败"
    exit 1
  }
  sleep 5
  BACKEND_STATUS="started"
fi

# 验证后端健康
if curl -s -f --max-time 5 http://localhost:8000/health >/dev/null 2>&1; then
  echo "✅ 后端健康检查通过"
else
  echo "⚠️  后端健康检查失败"
  echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
fi

# Step 2: 检查前端服务
echo ""
echo "[2/5] 检查前端服务..."
echo "----------------------------------------"
FRONTEND_SERVICE=""
if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
  FRONTEND_SERVICE="liaotian-frontend"
elif systemctl cat smart-tg-frontend.service >/dev/null 2>&1; then
  FRONTEND_SERVICE="smart-tg-frontend"
fi

if [ -n "$FRONTEND_SERVICE" ]; then
  if systemctl is-active "$FRONTEND_SERVICE" >/dev/null 2>&1; then
    echo "✅ 前端服务正在运行: $FRONTEND_SERVICE"
    FRONTEND_STATUS="running"
  else
    echo "⚠️  前端服务未运行，启动中..."
    sudo systemctl start "$FRONTEND_SERVICE" || {
      echo "⚠️  前端服务启动失败，但继续..."
    }
    sleep 5
    FRONTEND_STATUS="started"
  fi
  
  # 验证前端端口
  if sudo ss -tlnp 2>/dev/null | grep -q ":3000"; then
    echo "✅ 前端端口 3000 正在监听"
  else
    echo "⚠️  前端端口 3000 未监听"
    echo "  查看日志: sudo journalctl -u $FRONTEND_SERVICE -n 50 --no-pager"
  fi
else
  echo "⚠️  前端 systemd 服务未找到"
  echo "  检查是否有进程在端口 3000 上运行..."
  if sudo ss -tlnp 2>/dev/null | grep -q ":3000"; then
    echo "  ✅ 端口 3000 有进程在监听（可能是手动启动的）"
    FRONTEND_STATUS="manual"
  else
    echo "  ❌ 端口 3000 没有进程在监听"
    echo "  需要启动前端服务"
    FRONTEND_STATUS="missing"
  fi
fi

# Step 3: 检查 Nginx 配置
echo ""
echo "[3/5] 检查 Nginx 配置..."
echo "----------------------------------------"

# 检查配置文件是否存在
if [ -f "$PROJECT_DIR/deploy/nginx/aikz.conf" ]; then
  echo "✅ Nginx 配置文件存在"
  
  # 检查 upstream 配置
  if grep -q "upstream backend" "$PROJECT_DIR/deploy/nginx/aikz.conf"; then
    BACKEND_UPSTREAM=$(grep -A 2 "upstream backend" "$PROJECT_DIR/deploy/nginx/aikz.conf" | grep "server" | awk '{print $2}' || echo "")
    echo "  后端 upstream: $BACKEND_UPSTREAM"
  fi
  
  if grep -q "upstream frontend" "$PROJECT_DIR/deploy/nginx/aikz.conf"; then
    FRONTEND_UPSTREAM=$(grep -A 2 "upstream frontend" "$PROJECT_DIR/deploy/nginx/aikz.conf" | grep "server" | awk '{print $2}' || echo "")
    echo "  前端 upstream: $FRONTEND_UPSTREAM"
  fi
else
  echo "❌ Nginx 配置文件不存在"
  exit 1
fi

# 检查当前加载的配置
echo ""
echo "检查当前 Nginx 配置..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置语法错误"
  sudo nginx -t
  exit 1
fi

# Step 4: 更新 Nginx 配置
echo ""
echo "[4/5] 更新 Nginx 配置..."
echo "----------------------------------------"

# 复制配置文件
if [ -f "$PROJECT_DIR/deploy/nginx/aikz.conf" ]; then
  echo "复制 Nginx 配置文件..."
  sudo cp "$PROJECT_DIR/deploy/nginx/aikz.conf" /etc/nginx/sites-available/aikz.conf
  sudo ln -sf /etc/nginx/sites-available/aikz.conf /etc/nginx/sites-enabled/aikz.conf
  
  # 检查是否有重复的 server_name
  DUPLICATE_SERVERS=$(sudo grep -r "server_name aikz.usdt2026.cc" /etc/nginx/sites-enabled/ 2>/dev/null | wc -l || echo "0")
  if [ "$DUPLICATE_SERVERS" -gt 1 ]; then
    echo "⚠️  发现重复的 server_name 配置"
    echo "  检查其他配置文件..."
    sudo grep -r "server_name aikz.usdt2026.cc" /etc/nginx/sites-enabled/ 2>/dev/null || true
  fi
  
  # 测试配置
  if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置测试通过"
    # 重新加载 Nginx
    echo "重新加载 Nginx..."
    sudo systemctl reload nginx && echo "✅ Nginx 已重新加载" || {
      echo "❌ Nginx 重新加载失败"
      exit 1
    }
  else
    echo "❌ Nginx 配置测试失败"
    sudo nginx -t
    exit 1
  fi
else
  echo "❌ Nginx 配置文件不存在"
  exit 1
fi

# Step 5: 验证服务连接
echo ""
echo "[5/5] 验证服务连接..."
echo "----------------------------------------"

# 测试后端连接
echo "测试后端连接 (http://localhost:8000/health)..."
BACKEND_RESPONSE=$(curl -s --max-time 5 http://localhost:8000/health 2>/dev/null || echo "ERROR")
if [ "$BACKEND_RESPONSE" = '{"status":"ok"}' ] || [ "$BACKEND_RESPONSE" = '{"status": "ok"}' ]; then
  echo "✅ 后端连接正常: $BACKEND_RESPONSE"
else
  echo "❌ 后端连接失败: $BACKEND_RESPONSE"
fi

# 测试前端连接
echo "测试前端连接 (http://localhost:3000)..."
FRONTEND_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_HTTP_CODE" = "200" ] || [ "$FRONTEND_HTTP_CODE" = "301" ] || [ "$FRONTEND_HTTP_CODE" = "302" ]; then
  echo "✅ 前端连接正常 (HTTP $FRONTEND_HTTP_CODE)"
else
  echo "⚠️  前端连接失败 (HTTP $FRONTEND_HTTP_CODE)"
  if [ "$FRONTEND_STATUS" = "missing" ]; then
    echo "  前端服务未运行，需要启动前端服务"
  fi
fi

# 测试 Nginx 代理
echo "测试 Nginx 代理 (http://localhost/api/v1/health)..."
NGINX_API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost/api/v1/health 2>/dev/null || echo "000")
if [ "$NGINX_API_RESPONSE" = "200" ] || [ "$NGINX_API_RESPONSE" = "401" ] || [ "$NGINX_API_RESPONSE" = "403" ]; then
  echo "✅ Nginx API 代理正常 (HTTP $NGINX_API_RESPONSE)"
else
  echo "⚠️  Nginx API 代理失败 (HTTP $NGINX_API_RESPONSE)"
  echo "  检查 Nginx 错误日志: sudo tail -20 /var/log/nginx/error.log"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "服务状态:"
echo "  - 后端服务: $BACKEND_STATUS"
echo "  - 前端服务: $FRONTEND_STATUS"
echo ""
echo "如果前端服务未运行，请执行:"
echo "  cd $PROJECT_DIR/saas-demo"
echo "  npm run build"
echo "  # 然后启动前端服务或配置 systemd 服务"
echo ""
echo "验证命令:"
echo "  - 后端: curl http://localhost:8000/health"
echo "  - 前端: curl http://localhost:3000"
echo "  - Nginx API: curl http://localhost/api/v1/health"

