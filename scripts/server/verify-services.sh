#!/bin/bash
# ============================================================
# 验证服务是否正常运行
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
step_msg() { echo -e "${BLUE}📌 $1${NC}"; }

echo "========================================="
echo "验证服务运行状态"
echo "========================================="
echo ""

# 1. 检查 PM2 状态
step_msg "[1/5] 检查 PM2 服务状态..."
if command -v pm2 > /dev/null 2>&1; then
    pm2 status
    echo ""
    
    BACKEND_STATUS=$(pm2 jlist | jq -r '.[] | select(.name=="backend") | .pm2_env.status' 2>/dev/null || echo "unknown")
    FRONTEND_STATUS=$(pm2 jlist | jq -r '.[] | select(.name=="frontend") | .pm2_env.status' 2>/dev/null || echo "unknown")
    
    if [ "$BACKEND_STATUS" = "online" ]; then
        success_msg "后端服务: online"
    else
        error_msg "后端服务: $BACKEND_STATUS"
    fi
    
    if [ "$FRONTEND_STATUS" = "online" ]; then
        success_msg "前端服务: online"
    else
        error_msg "前端服务: $FRONTEND_STATUS"
    fi
else
    error_msg "PM2 未安装或不在 PATH 中"
fi
echo ""

# 2. 检查端口监听
step_msg "[2/5] 检查端口监听..."

if sudo ss -tlnp | grep -q ":8000 "; then
    success_msg "端口 8000 (后端) 正在监听"
    sudo ss -tlnp | grep ":8000" | head -1
else
    error_msg "端口 8000 (后端) 未监听"
fi

if sudo ss -tlnp | grep -q ":3000 "; then
    success_msg "端口 3000 (前端) 正在监听"
    sudo ss -tlnp | grep ":3000" | head -1
else
    error_msg "端口 3000 (前端) 未监听"
fi
echo ""

# 3. 测试后端健康检查
step_msg "[3/5] 测试后端健康检查..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/health 2>/dev/null || echo "000")

if [ "$BACKEND_HEALTH" = "200" ]; then
    success_msg "后端健康检查: HTTP 200"
    curl -s http://localhost:8000/health | head -3
    echo ""
else
    error_msg "后端健康检查失败: HTTP $BACKEND_HEALTH"
fi
echo ""

# 4. 测试前端服务
step_msg "[4/5] 测试前端服务..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000 2>/dev/null || echo "000")

if [ "$FRONTEND_RESPONSE" = "200" ] || [ "$FRONTEND_RESPONSE" = "304" ]; then
    success_msg "前端服务: HTTP $FRONTEND_RESPONSE"
    echo "前端响应正常"
else
    error_msg "前端服务响应失败: HTTP $FRONTEND_RESPONSE"
fi
echo ""

# 5. 查看最近日志
step_msg "[5/5] 查看最近日志（最后 10 行）..."
if command -v pm2 > /dev/null 2>&1; then
    echo "--- 后端日志 (最后 10 行) ---"
    pm2 logs backend --lines 10 --nostream 2>/dev/null || echo "无法获取后端日志"
    echo ""
    echo "--- 前端日志 (最后 10 行) ---"
    pm2 logs frontend --lines 10 --nostream 2>/dev/null || echo "无法获取前端日志"
fi
echo ""

# 总结
echo "========================================="
echo "验证完成"
echo "========================================="

ALL_OK=true
if [ "$BACKEND_STATUS" != "online" ] || [ "$BACKEND_HEALTH" != "200" ]; then
    error_msg "后端服务存在问题"
    ALL_OK=false
fi

if [ "$FRONTEND_STATUS" != "online" ] || [ "$FRONTEND_RESPONSE" != "200" ] && [ "$FRONTEND_RESPONSE" != "304" ]; then
    error_msg "前端服务存在问题"
    ALL_OK=false
fi

if [ "$ALL_OK" = "true" ]; then
    success_msg "所有服务运行正常！"
    echo ""
    echo "✅ 后端: http://localhost:8000"
    echo "✅ 前端: http://localhost:3000"
    echo ""
    echo "下一步：配置 Nginx 反向代理"
else
    error_msg "部分服务存在问题，请检查日志"
    echo ""
    echo "查看详细日志："
    echo "  pm2 logs backend"
    echo "  pm2 logs frontend"
fi
