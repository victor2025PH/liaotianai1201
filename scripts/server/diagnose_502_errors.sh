#!/bin/bash
# ============================================================
# Diagnose 502 Bad Gateway Errors (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Diagnose and fix 502 Bad Gateway errors
#
# One-click execution: sudo bash scripts/server/diagnose_502_errors.sh
# ============================================================

set -e

echo "============================================================"
echo "🔍 诊断 502 Bad Gateway 错误"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 步骤 1: 检查后端服务状态
echo "[1/5] 检查后端服务状态"
echo "----------------------------------------"
if systemctl is-active --quiet luckyred-api 2>/dev/null; then
  echo -e "${GREEN}✅ luckyred-api 服务运行中${NC}"
  systemctl status luckyred-api --no-pager | head -10
else
  echo -e "${RED}❌ luckyred-api 服务未运行${NC}"
  echo "尝试启动服务..."
  sudo systemctl start luckyred-api
  sleep 3
  if systemctl is-active --quiet luckyred-api 2>/dev/null; then
    echo -e "${GREEN}✅ 服务已启动${NC}"
  else
    echo -e "${RED}❌ 服务启动失败${NC}"
    echo "查看服务日志:"
    sudo journalctl -u luckyred-api -n 30 --no-pager | tail -20
  fi
fi

echo ""

# 步骤 2: 检查端口监听
echo "[2/5] 检查端口监听"
echo "----------------------------------------"
if ss -tlnp | grep -q ":8000"; then
  echo -e "${GREEN}✅ 端口 8000 正在监听${NC}"
  ss -tlnp | grep ":8000"
else
  echo -e "${RED}❌ 端口 8000 未监听${NC}"
  echo "后端服务可能未正常启动"
fi

echo ""

# 步骤 3: 测试本地 API 访问
echo "[3/5] 测试本地 API 访问"
echo "----------------------------------------"
API_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:8000/api/v1/health" 2>/dev/null || echo "000")
if [ "$API_TEST" = "200" ] || [ "$API_TEST" = "401" ] || [ "$API_TEST" = "404" ]; then
  echo -e "${GREEN}✅ 本地 API 访问正常: HTTP $API_TEST${NC}"
else
  echo -e "${RED}❌ 本地 API 访问失败: HTTP $API_TEST${NC}"
  echo "后端服务可能有问题"
fi

# 测试 workers API
WORKERS_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://127.0.0.1:8000/api/v1/workers/" 2>/dev/null || echo "000")
if [ "$WORKERS_TEST" = "200" ] || [ "$WORKERS_TEST" = "401" ] || [ "$WORKERS_TEST" = "404" ]; then
  echo -e "${GREEN}✅ Workers API 访问正常: HTTP $WORKERS_TEST${NC}"
else
  echo -e "${YELLOW}⚠️  Workers API 访问异常: HTTP $WORKERS_TEST${NC}"
fi

echo ""

# 步骤 4: 检查 Nginx 配置
echo "[4/5] 检查 Nginx 配置"
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/default"
if [ -f "$NGINX_CONFIG" ]; then
  # 检查 API 代理配置
  if grep -q "location /api/" "$NGINX_CONFIG" && grep -q "proxy_pass.*8000" "$NGINX_CONFIG"; then
    echo -e "${GREEN}✅ Nginx API 代理配置存在${NC}"
  else
    echo -e "${RED}❌ Nginx API 代理配置缺失或错误${NC}"
  fi
  
  # 检查 WebSocket 配置
  if grep -q "location /api/v1/notifications/ws" "$NGINX_CONFIG"; then
    echo -e "${GREEN}✅ Nginx WebSocket 配置存在${NC}"
  else
    echo -e "${YELLOW}⚠️  Nginx WebSocket 配置缺失${NC}"
  fi
  
  # 测试 Nginx 配置
  if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    echo -e "${GREEN}✅ Nginx 配置语法正确${NC}"
  else
    echo -e "${RED}❌ Nginx 配置语法错误${NC}"
    sudo nginx -t 2>&1 | tail -5
  fi
else
  echo -e "${RED}❌ Nginx 配置文件不存在${NC}"
fi

echo ""

# 步骤 5: 检查后端日志
echo "[5/5] 检查后端日志（最近错误）"
echo "----------------------------------------"
if systemctl is-active --quiet luckyred-api 2>/dev/null; then
  echo "后端服务日志（最后 20 行）:"
  sudo journalctl -u luckyred-api -n 20 --no-pager | tail -20 || echo "无法读取日志"
else
  echo "服务未运行，无法查看日志"
fi

echo ""
echo "============================================================"
echo "📋 诊断摘要"
echo "============================================================"
echo ""
echo "如果后端服务未运行，请执行："
echo "  sudo systemctl restart luckyred-api"
echo ""
echo "如果端口未监听，请检查："
echo "  1. 后端服务是否正常启动"
echo "  2. 查看服务日志: sudo journalctl -u luckyred-api -n 50 --no-pager"
echo ""
echo "如果 Nginx 配置有问题，请执行："
echo "  bash scripts/server/fix-nginx-routes-complete.sh"
echo ""

