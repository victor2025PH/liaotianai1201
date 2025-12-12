#!/bin/bash
# ============================================================
# 诊断后端连接问题
# ============================================================

echo "=========================================="
echo "诊断后端连接问题"
echo "=========================================="
echo ""

# 1. 检查后端服务状态
echo "[1/5] 检查后端服务状态..."
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
  BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
  BACKEND_SERVICE="telegram-backend"
fi

if [ -n "$BACKEND_SERVICE" ]; then
  echo "  后端服务: $BACKEND_SERVICE"
  STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
  echo "  状态: $STATUS"
  
  if [ "$STATUS" != "active" ]; then
    echo "  ⚠️  后端服务未运行！"
    echo "  尝试启动: sudo systemctl start $BACKEND_SERVICE"
  fi
else
  echo "  ❌ 后端服务未找到"
fi

echo ""

# 2. 检查端口8000
echo "[2/5] 检查端口8000..."
PORT_8000=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
if [ -n "$PORT_8000" ]; then
  echo "  ✅ 端口8000正在监听"
  echo "  $PORT_8000"
else
  echo "  ❌ 端口8000未监听"
  echo "  后端服务可能未启动"
fi

echo ""

# 3. 测试本地连接
echo "[3/5] 测试本地API连接..."
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
  echo "  ✅ 本地API连接成功"
  curl -s http://localhost:8000/health | head -5
else
  echo "  ❌ 本地API连接失败"
  echo "  错误: 无法连接到 http://localhost:8000/health"
fi

echo ""

# 4. 检查Nginx配置
echo "[4/5] 检查Nginx配置..."
if [ -f "/etc/nginx/sites-available/aikz.conf" ]; then
  echo "  ✅ Nginx配置文件存在"
  
  # 检查upstream配置
  if grep -q "server localhost:8000" /etc/nginx/sites-available/aikz.conf; then
    echo "  ✅ Backend upstream配置正确"
  else
    echo "  ⚠️  Backend upstream配置可能有问题"
  fi
  
  # 检查Nginx状态
  if systemctl is-active --quiet nginx; then
    echo "  ✅ Nginx服务运行中"
  else
    echo "  ❌ Nginx服务未运行"
    echo "  启动: sudo systemctl start nginx"
  fi
else
  echo "  ⚠️  Nginx配置文件不存在"
fi

echo ""

# 5. 检查后端日志
echo "[5/5] 检查后端服务日志（最近20行）..."
if [ -n "$BACKEND_SERVICE" ]; then
  echo "  服务: $BACKEND_SERVICE"
  sudo journalctl -u "$BACKEND_SERVICE" -n 20 --no-pager | tail -15
else
  echo "  ⚠️  无法检查日志（服务未找到）"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果后端服务未运行，执行："
echo "  sudo systemctl start $BACKEND_SERVICE"
echo ""
echo "如果端口8000被占用，执行："
echo "  bash scripts/server/fix-port-8000.sh"
echo ""

