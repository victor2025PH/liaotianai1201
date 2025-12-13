#!/bin/bash
# ============================================================
# 启动并验证所有服务
# ============================================================

set -e

echo "=========================================="
echo "启动并验证所有服务"
echo "=========================================="

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="luckyred-api"
FRONTEND_SERVICE="liaotian-frontend"

# Step 1: 确保数据库表存在
echo ""
echo "[1/5] 确保数据库表存在..."
echo "----------------------------------------"
cd "$PROJECT_DIR/admin-backend" || exit 1

if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
  
  # 运行数据库迁移
  echo "运行数据库迁移..."
  alembic upgrade head 2>&1 | tail -5 || {
    echo "⚠️  数据库迁移失败，尝试手动创建表..."
    python3 -c "
from app.db import Base, engine
from app.models.group_ai import AIProviderConfig, AIProviderSettings
Base.metadata.create_all(engine)
print('✅ 数据库表已创建')
" || echo "⚠️  创建表失败"
  }
  
  echo "✅ 数据库检查完成"
else
  echo "⚠️  虚拟环境不存在"
fi

# Step 2: 启动后端服务
echo ""
echo "[2/5] 启动后端服务..."
echo "----------------------------------------"

# 清理端口
PORT_8000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":8000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || true)
if [ -n "$PORT_8000_PID" ]; then
  echo "清理端口 8000 (PID: $PORT_8000_PID)..."
  sudo kill -9 "$PORT_8000_PID" 2>/dev/null || true
  sleep 2
fi

# 启动服务
if systemctl cat "$BACKEND_SERVICE" >/dev/null 2>&1; then
  echo "启动 $BACKEND_SERVICE..."
  sudo systemctl start "$BACKEND_SERVICE" || {
    echo "❌ 启动失败"
    exit 1
  }
  
  # 等待服务启动
  echo "等待服务启动（最多 30 秒）..."
  for i in {1..30}; do
    sleep 1
    if systemctl is-active "$BACKEND_SERVICE" >/dev/null 2>&1; then
      echo "✅ 服务已启动"
      break
    fi
    if [ $((i % 5)) -eq 0 ]; then
      echo "  等待中... ($i/30)"
    fi
  done
else
  echo "❌ 服务配置文件不存在"
  exit 1
fi

# Step 3: 验证后端健康
echo ""
echo "[3/5] 验证后端健康..."
echo "----------------------------------------"
sleep 3

# 健康检查
HEALTH_RESPONSE=$(curl -s --max-time 5 http://localhost:8000/health 2>/dev/null || echo "ERROR")
if [ "$HEALTH_RESPONSE" = '{"status":"ok"}' ] || [ "$HEALTH_RESPONSE" = '{"status": "ok"}' ]; then
  echo "✅ 后端健康检查通过"
else
  echo "⚠️  后端健康检查失败: $HEALTH_RESPONSE"
  echo "  查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50 --no-pager"
fi

# 测试 AI Provider API
echo "测试 AI Provider API..."
API_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/v1/group-ai/ai-provider/providers 2>/dev/null || echo "ERROR")
API_CODE=$(echo "$API_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")
API_BODY=$(echo "$API_RESPONSE" | grep -v "HTTP_CODE" | head -5 || echo "")

if [ "$API_CODE" = "200" ]; then
  echo "✅ AI Provider API 正常 (HTTP $API_CODE)"
elif [ "$API_CODE" = "401" ] || [ "$API_CODE" = "403" ]; then
  echo "✅ AI Provider API 可访问 (HTTP $API_CODE - 需要认证，这是正常的)"
else
  echo "❌ AI Provider API 失败 (HTTP $API_CODE)"
  echo "  响应: $API_BODY"
  echo "  查看详细日志: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager | grep -i error"
fi

# Step 4: 启动前端服务
echo ""
echo "[4/5] 启动前端服务..."
echo "----------------------------------------"

if systemctl cat "$FRONTEND_SERVICE" >/dev/null 2>&1; then
  # 检查前端是否已构建
  if [ ! -d "$PROJECT_DIR/saas-demo/.next/standalone" ]; then
    echo "⚠️  前端未构建，需要先构建..."
    echo "  执行: cd $PROJECT_DIR/saas-demo && npm run build"
  else
    echo "启动 $FRONTEND_SERVICE..."
    sudo systemctl start "$FRONTEND_SERVICE" || {
      echo "⚠️  前端服务启动失败，但继续..."
    }
    
    # 等待服务启动
    sleep 5
    
    # 检查端口
    if sudo ss -tlnp 2>/dev/null | grep -q ":3000"; then
      echo "✅ 前端端口 3000 正在监听"
    else
      echo "⚠️  前端端口 3000 未监听"
      echo "  查看日志: sudo journalctl -u $FRONTEND_SERVICE -n 50 --no-pager"
    fi
  fi
else
  echo "⚠️  前端服务配置文件不存在"
fi

# Step 5: 验证 Nginx 配置
echo ""
echo "[5/5] 验证 Nginx 配置..."
echo "----------------------------------------"

# 检查 Nginx 配置
if sudo nginx -t 2>&1 | grep -q "successful"; then
  echo "✅ Nginx 配置正确"
  
  # 重新加载 Nginx
  sudo systemctl reload nginx && echo "✅ Nginx 已重新加载" || echo "⚠️  Nginx 重新加载失败"
else
  echo "❌ Nginx 配置错误"
  sudo nginx -t
fi

# 测试 Nginx 代理
echo "测试 Nginx API 代理..."
NGINX_API_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost/api/v1/health 2>/dev/null || echo "000")
if [ "$NGINX_API_CODE" = "200" ] || [ "$NGINX_API_CODE" = "401" ] || [ "$NGINX_API_CODE" = "403" ]; then
  echo "✅ Nginx API 代理正常 (HTTP $NGINX_API_CODE)"
else
  echo "⚠️  Nginx API 代理失败 (HTTP $NGINX_API_CODE)"
  echo "  检查 Nginx 错误日志: sudo tail -20 /var/log/nginx/error.log"
fi

echo ""
echo "=========================================="
echo "验证完成"
echo "=========================================="
echo ""
echo "服务状态:"
echo "  - 后端服务: $(systemctl is-active $BACKEND_SERVICE 2>/dev/null || echo 'unknown')"
echo "  - 前端服务: $(systemctl is-active $FRONTEND_SERVICE 2>/dev/null || echo 'unknown')"
echo "  - Nginx: $(systemctl is-active nginx 2>/dev/null || echo 'unknown')"
echo ""
echo "如果仍有问题，请查看日志:"
echo "  - 后端: sudo journalctl -u $BACKEND_SERVICE -n 100 --no-pager"
echo "  - 前端: sudo journalctl -u $FRONTEND_SERVICE -n 50 --no-pager"
echo "  - Nginx: sudo tail -50 /var/log/nginx/error.log"

