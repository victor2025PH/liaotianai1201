#!/bin/bash
# ============================================================
# 后端 API 服务检查脚本
# ============================================================

set -e

echo "=========================================="
echo "🔍 后端 API 服务检查"
echo "=========================================="
echo ""

API_BASE="${API_BASE:-https://aikz.usdt2026.cc/api/v1}"
HEALTH_ENDPOINT="${API_BASE%/api/v1}/health"
HEARTBEAT_ENDPOINT="${API_BASE}/workers/heartbeat"

echo "API 配置:"
echo "  - API 基础 URL: $API_BASE"
echo "  - 健康检查端点: $HEALTH_ENDPOINT"
echo "  - 心跳端点: $HEARTBEAT_ENDPOINT"
echo ""

# 1. 检查本地后端服务
echo "[1/4] 检查本地后端服务..."
BACKEND_SERVICE=""
if systemctl cat luckyred-api.service >/dev/null 2>&1; then
    BACKEND_SERVICE="luckyred-api"
elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
    BACKEND_SERVICE="telegram-backend"
fi

if [ -n "$BACKEND_SERVICE" ]; then
    echo "  检测到的后端服务: $BACKEND_SERVICE"
    SERVICE_STATUS=$(systemctl is-active "$BACKEND_SERVICE" 2>/dev/null || echo "unknown")
    if [ "$SERVICE_STATUS" = "active" ]; then
        echo "  ✅ 后端服务正在运行"
    else
        echo "  ❌ 后端服务未运行 (状态: $SERVICE_STATUS)"
        echo "    启动命令: sudo systemctl start $BACKEND_SERVICE"
    fi
    
    # 检查端口监听
    PORT_8000=$(sudo ss -tlnp 2>/dev/null | grep ":8000" || echo "")
    if [ -n "$PORT_8000" ]; then
        echo "  ✅ 端口 8000 正在监听"
    else
        echo "  ❌ 端口 8000 未监听"
    fi
else
    echo "  ⚠️  未找到后端 systemd 服务"
fi
echo ""

# 2. 测试本地健康检查
echo "[2/4] 测试本地健康检查..."
LOCAL_HEALTH=$(curl -s --connect-timeout 5 http://localhost:8000/health 2>/dev/null || echo "")
if [ -n "$LOCAL_HEALTH" ]; then
    echo "  ✅ 本地健康检查成功"
    echo "    响应: $LOCAL_HEALTH" | head -c 100
    echo ""
else
    echo "  ❌ 本地健康检查失败"
    echo "    请检查后端服务是否运行在端口 8000"
fi
echo ""

# 3. 测试公共 API 健康检查
echo "[3/4] 测试公共 API 健康检查..."
PUBLIC_HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")
if [ "$PUBLIC_HEALTH_CODE" = "200" ]; then
    echo "  ✅ 公共健康检查成功 (状态码: $PUBLIC_HEALTH_CODE)"
    PUBLIC_HEALTH_RESPONSE=$(curl -s --connect-timeout 10 "$HEALTH_ENDPOINT" 2>/dev/null || echo "")
    if [ -n "$PUBLIC_HEALTH_RESPONSE" ]; then
        echo "    响应: $PUBLIC_HEALTH_RESPONSE" | head -c 100
        echo ""
    fi
else
    echo "  ❌ 公共健康检查失败 (状态码: $PUBLIC_HEALTH_CODE)"
    echo "    请检查 Nginx 配置和后端服务"
fi
echo ""

# 4. 测试心跳端点
echo "[4/4] 测试心跳端点..."
HEARTBEAT_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --connect-timeout 10 -X POST "$HEARTBEAT_ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{"node_id":"diagnostic-test","status":"online","account_count":0,"accounts":[],"metadata":{}}' 2>/dev/null || echo "ERROR")
HEARTBEAT_HTTP_CODE=$(echo "$HEARTBEAT_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2 || echo "000")
HEARTBEAT_BODY=$(echo "$HEARTBEAT_RESPONSE" | grep -v "HTTP_CODE" || echo "")

if [ "$HEARTBEAT_HTTP_CODE" = "200" ]; then
    echo "  ✅ 心跳端点可访问 (状态码: $HEARTBEAT_HTTP_CODE)"
    if [ -n "$HEARTBEAT_BODY" ]; then
        echo "    响应: $HEARTBEAT_BODY" | head -c 200
        echo ""
    fi
elif [ "$HEARTBEAT_HTTP_CODE" = "401" ] || [ "$HEARTBEAT_HTTP_CODE" = "403" ]; then
    echo "  ⚠️  心跳端点需要认证 (状态码: $HEARTBEAT_HTTP_CODE)"
    echo "    这是正常的，Worker 节点需要提供认证信息"
elif [ "$HEARTBEAT_HTTP_CODE" = "404" ]; then
    echo "  ❌ 心跳端点不存在 (状态码: $HEARTBEAT_HTTP_CODE)"
    echo "    请检查 API 路由配置"
else
    echo "  ❌ 心跳端点不可访问 (状态码: $HEARTBEAT_HTTP_CODE)"
    if [ -n "$HEARTBEAT_BODY" ]; then
        echo "    错误信息: $HEARTBEAT_BODY" | head -c 200
        echo ""
    fi
fi
echo ""

# 总结
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""
echo "建议："
if [ "$SERVICE_STATUS" != "active" ]; then
    echo "  1. 启动后端服务: sudo systemctl start $BACKEND_SERVICE"
fi
if [ "$PUBLIC_HEALTH_CODE" != "200" ]; then
    echo "  2. 检查 Nginx 配置: sudo nginx -t"
    echo "  3. 重新加载 Nginx: sudo systemctl reload nginx"
fi
if [ "$HEARTBEAT_HTTP_CODE" = "404" ]; then
    echo "  4. 检查 API 路由注册: grep -r 'workers/heartbeat' admin-backend/app/api/"
fi
echo ""

