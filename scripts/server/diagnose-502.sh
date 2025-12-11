#!/bin/bash
# ============================================================
# 诊断 502 Bad Gateway 错误脚本
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "◆ 诊断 502 Bad Gateway 错误"
echo "============================================================"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}▲ 提示：某些命令需要 sudo 权限${NC}"
    SUDO="sudo"
else
    SUDO=""
fi

echo "[1] 检查后端服务状态（端口 8000）..."
echo "----------------------------------------"
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
    BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
    BACKEND_SERVICE="telegram-backend"
fi

if [ -n "$BACKEND_SERVICE" ]; then
    BACKEND_STATUS=$($SUDO systemctl is-active "$BACKEND_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || echo "inactive")
    echo "  服务名称: $BACKEND_SERVICE"
    echo "  服务状态: $BACKEND_STATUS"
    
    if [ "$BACKEND_STATUS" = "active" ]; then
        echo -e "  ${GREEN}□ 后端服务正在运行${NC}"
    else
        echo -e "  ${RED}❌ 后端服务未运行${NC}"
        echo "  最近 10 行日志:"
        $SUDO journalctl -u "$BACKEND_SERVICE" -n 10 --no-pager | tail -10 || true
    fi
else
    echo -e "  ${RED}❌ 未找到后端服务${NC}"
fi

# 检查端口 8000
echo ""
echo "  端口 8000 监听状态:"
PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
if [ -n "$PORT_8000" ]; then
    echo -e "  ${GREEN}□ 端口 8000 正在监听${NC}"
    echo "  $PORT_8000"
else
    echo -e "  ${RED}❌ 端口 8000 未监听${NC}"
fi

# 测试后端连接
echo ""
echo "  测试后端连接:"
if timeout 5s curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "  ${GREEN}□ 后端健康检查通过${NC}"
else
    echo -e "  ${RED}❌ 后端健康检查失败${NC}"
fi
echo ""

echo "[2] 检查前端服务状态（端口 3000）..."
echo "----------------------------------------"
FRONTEND_SERVICE=""
if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
    FRONTEND_SERVICE="liaotian-frontend"
elif systemctl cat smart-tg-frontend.service >/dev/null 2>&1; then
    FRONTEND_SERVICE="smart-tg-frontend"
fi

if [ -n "$FRONTEND_SERVICE" ]; then
    FRONTEND_STATUS=$($SUDO systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null | awk 'NR==1 {print $1}' || echo "inactive")
    echo "  服务名称: $FRONTEND_SERVICE"
    echo "  服务状态: $FRONTEND_STATUS"
    
    if [ "$FRONTEND_STATUS" = "active" ]; then
        echo -e "  ${GREEN}□ 前端服务正在运行${NC}"
    else
        echo -e "  ${RED}❌ 前端服务未运行${NC}"
        echo "  最近 10 行日志:"
        $SUDO journalctl -u "$FRONTEND_SERVICE" -n 10 --no-pager | tail -10 || true
    fi
else
    echo -e "  ${YELLOW}▲ 未找到前端服务（可能未配置）${NC}"
fi

# 检查端口 3000
echo ""
echo "  端口 3000 监听状态:"
PORT_3000=$(sudo ss -tlnp | grep ":3000" || echo "")
if [ -n "$PORT_3000" ]; then
    echo -e "  ${GREEN}□ 端口 3000 正在监听${NC}"
    echo "  $PORT_3000"
else
    echo -e "  ${RED}❌ 端口 3000 未监听${NC}"
fi

# 测试前端连接
echo ""
echo "  测试前端连接:"
if timeout 5s curl -s -f http://localhost:3000 >/dev/null 2>&1; then
    echo -e "  ${GREEN}□ 前端连接成功${NC}"
else
    echo -e "  ${RED}❌ 前端连接失败${NC}"
fi
echo ""

echo "[3] 检查 Nginx 状态..."
echo "----------------------------------------"
NGINX_STATUS=$($SUDO systemctl is-active nginx 2>/dev/null | awk 'NR==1 {print $1}' || echo "inactive")
if [ "$NGINX_STATUS" = "active" ]; then
    echo -e "  ${GREEN}□ Nginx 正在运行${NC}"
else
    echo -e "  ${RED}❌ Nginx 未运行${NC}"
fi

echo ""
echo "  Nginx 错误日志（最近 10 行）:"
$SUDO tail -10 /var/log/nginx/aikz-error.log 2>/dev/null || $SUDO tail -10 /var/log/nginx/error.log 2>/dev/null || echo "  (无法读取日志)"
echo ""

echo "[4] 检查 Nginx 配置..."
echo "----------------------------------------"
if $SUDO nginx -t 2>&1 | grep -q "successful"; then
    echo -e "  ${GREEN}□ Nginx 配置有效${NC}"
else
    echo -e "  ${RED}❌ Nginx 配置有错误${NC}"
    $SUDO nginx -t 2>&1 | head -5 || true
fi
echo ""

echo "[5] 诊断总结和建议..."
echo "----------------------------------------"
ISSUES=0

if [ -z "$PORT_8000" ]; then
    echo -e "  ${RED}❌ 问题 1: 后端服务（端口 8000）未监听${NC}"
    echo "     建议: 检查后端服务是否启动，查看日志: sudo journalctl -u $BACKEND_SERVICE -n 50"
    ISSUES=$((ISSUES + 1))
fi

if [ -z "$PORT_3000" ]; then
    echo -e "  ${RED}❌ 问题 2: 前端服务（端口 3000）未监听${NC}"
    echo "     建议: 检查前端服务是否启动，查看日志: sudo journalctl -u $FRONTEND_SERVICE -n 50"
    ISSUES=$((ISSUES + 1))
fi

if [ "$NGINX_STATUS" != "active" ]; then
    echo -e "  ${RED}❌ 问题 3: Nginx 未运行${NC}"
    echo "     建议: 启动 Nginx: sudo systemctl start nginx"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "  ${GREEN}□ 所有服务看起来正常，如果仍有 502 错误，请检查防火墙或网络配置${NC}"
else
    echo ""
    echo -e "  ${YELLOW}▲ 发现 $ISSUES 个问题，请根据上述建议进行修复${NC}"
fi

echo ""
echo "============================================================"
echo "诊断完成"
echo "============================================================"

