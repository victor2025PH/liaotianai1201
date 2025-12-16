#!/bin/bash
# ============================================================
# Fix 502 Bad Gateway Errors (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Fix 502 Bad Gateway errors by restarting services and fixing Nginx
#
# One-click execution: sudo bash scripts/server/fix_502_errors.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 修复 502 Bad Gateway 错误"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
NGINX_CONFIG="/etc/nginx/sites-available/default"

# 步骤 1: 重启后端服务
echo "[1/4] 重启后端服务"
echo "----------------------------------------"
echo "停止 luckyred-api 服务..."
sudo systemctl stop luckyred-api 2>/dev/null || true
sleep 2

echo "启动 luckyred-api 服务..."
sudo systemctl start luckyred-api
sleep 5

if systemctl is-active --quiet luckyred-api 2>/dev/null; then
  echo -e "${GREEN}✅ 后端服务已启动${NC}"
  systemctl status luckyred-api --no-pager | head -10
else
  echo -e "${RED}❌ 后端服务启动失败${NC}"
  echo "查看错误日志:"
  sudo journalctl -u luckyred-api -n 30 --no-pager | tail -20
  exit 1
fi

echo ""

# 步骤 2: 检查端口监听
echo "[2/4] 检查端口监听"
echo "----------------------------------------"
sleep 3
if ss -tlnp | grep -q ":8000"; then
  echo -e "${GREEN}✅ 端口 8000 正在监听${NC}"
  ss -tlnp | grep ":8000"
else
  echo -e "${RED}❌ 端口 8000 未监听，后端服务可能有问题${NC}"
  echo "查看服务日志:"
  sudo journalctl -u luckyred-api -n 50 --no-pager | tail -30
  exit 1
fi

echo ""

# 步骤 3: 测试本地 API
echo "[3/4] 测试本地 API 访问"
echo "----------------------------------------"
API_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:8000/api/v1/health" 2>/dev/null || echo "000")
if [ "$API_TEST" = "200" ] || [ "$API_TEST" = "401" ] || [ "$API_TEST" = "404" ]; then
  echo -e "${GREEN}✅ 本地 API 访问正常: HTTP $API_TEST${NC}"
else
  echo -e "${YELLOW}⚠️  本地 API 访问异常: HTTP $API_TEST（可能需要更多时间启动）${NC}"
  echo "等待 10 秒后重试..."
  sleep 10
  API_TEST2=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:8000/api/v1/health" 2>/dev/null || echo "000")
  if [ "$API_TEST2" = "200" ] || [ "$API_TEST2" = "401" ] || [ "$API_TEST2" = "404" ]; then
    echo -e "${GREEN}✅ 重试后 API 访问正常: HTTP $API_TEST2${NC}"
  else
    echo -e "${RED}❌ API 仍然无法访问: HTTP $API_TEST2${NC}"
    echo "请检查后端服务日志: sudo journalctl -u luckyred-api -n 50 --no-pager"
  fi
fi

echo ""

# 步骤 4: 检查并修复 Nginx 配置
echo "[4/4] 检查并修复 Nginx 配置"
echo "----------------------------------------"

# 备份 Nginx 配置
if [ -f "$NGINX_CONFIG" ]; then
  BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
  sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
  echo "✅ 已备份 Nginx 配置到: $BACKUP_FILE"
fi

# 检查 API 代理配置
if ! grep -q "location /api/" "$NGINX_CONFIG" || ! grep -q "proxy_pass.*8000" "$NGINX_CONFIG"; then
  echo -e "${YELLOW}⚠️  Nginx API 代理配置缺失，尝试修复...${NC}"
  
  # 检查是否有修复脚本
  if [ -f "$PROJECT_DIR/scripts/server/fix-nginx-routes-complete.sh" ]; then
    echo "执行 Nginx 修复脚本..."
    bash "$PROJECT_DIR/scripts/server/fix-nginx-routes-complete.sh"
  else
    echo -e "${RED}❌ Nginx 修复脚本不存在，请手动检查配置${NC}"
  fi
else
  echo -e "${GREEN}✅ Nginx API 代理配置存在${NC}"
fi

# 检查 WebSocket 配置
if ! grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
  echo -e "${YELLOW}⚠️  Nginx WebSocket 配置缺失${NC}"
  echo "WebSocket 功能可能无法正常工作"
else
  echo -e "${GREEN}✅ Nginx WebSocket 配置存在${NC}"
fi

# 测试 Nginx 配置
if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
  echo -e "${GREEN}✅ Nginx 配置语法正确${NC}"
  echo "重新加载 Nginx..."
  sudo systemctl reload nginx
  echo -e "${GREEN}✅ Nginx 已重新加载${NC}"
else
  echo -e "${RED}❌ Nginx 配置语法错误${NC}"
  sudo nginx -t 2>&1 | tail -10
  echo "请修复配置后重试"
  exit 1
fi

echo ""

# 最终验证
echo "============================================================"
echo "✅ 修复完成 - 最终验证"
echo "============================================================"
echo ""

sleep 3

# 测试外部访问（通过 Nginx）
DOMAIN="${SERVER_HOST:-aikz.usdt2026.cc}"
echo "测试外部 API 访问（通过 Nginx）..."
HTTPS_API_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://${DOMAIN}/api/v1/health" 2>/dev/null || echo "000")

if [ "$HTTPS_API_TEST" = "200" ] || [ "$HTTPS_API_TEST" = "401" ] || [ "$HTTPS_API_TEST" = "404" ]; then
  echo -e "${GREEN}✅ 外部 API 访问正常: HTTP $HTTPS_API_TEST${NC}"
else
  echo -e "${YELLOW}⚠️  外部 API 访问异常: HTTP $HTTPS_API_TEST${NC}"
  echo "可能需要等待几秒钟让服务完全启动"
fi

# 测试 Workers API
HTTPS_WORKERS_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://${DOMAIN}/api/v1/workers/" 2>/dev/null || echo "000")
if [ "$HTTPS_WORKERS_TEST" = "200" ] || [ "$HTTPS_WORKERS_TEST" = "401" ] || [ "$HTTPS_WORKERS_TEST" = "404" ]; then
  echo -e "${GREEN}✅ Workers API 访问正常: HTTP $HTTPS_WORKERS_TEST${NC}"
else
  echo -e "${YELLOW}⚠️  Workers API 访问异常: HTTP $HTTPS_WORKERS_TEST${NC}"
fi

echo ""
echo "============================================================"
echo "✅ 修复流程完成"
echo "============================================================"
echo ""
echo "如果问题仍然存在，请执行诊断脚本："
echo "  sudo bash scripts/server/diagnose_502_errors.sh"
echo ""

