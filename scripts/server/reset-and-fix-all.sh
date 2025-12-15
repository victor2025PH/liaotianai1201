#!/bin/bash
# ============================================================
# 一键重置 Nginx 配置并检查/启动所有服务
# ============================================================

set +e

echo "=========================================="
echo "🚀 一键重置 Nginx 并启动所有服务"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 重置 Nginx 配置
echo "[1/3] 重置 Nginx 配置..."
echo "=========================================="
if [ -f "$PROJECT_DIR/scripts/server/reset-nginx-config.sh" ]; then
    bash "$PROJECT_DIR/scripts/server/reset-nginx-config.sh"
    if [ $? -ne 0 ]; then
        echo "❌ Nginx 配置重置失败"
        exit 1
    fi
else
    echo "❌ 重置脚本不存在: $PROJECT_DIR/scripts/server/reset-nginx-config.sh"
    exit 1
fi
echo ""

# 2. 检查并启动后端服务
echo "[2/3] 检查并启动后端服务..."
echo "=========================================="
if [ -f "$PROJECT_DIR/scripts/server/check-and-start-services.sh" ]; then
    bash "$PROJECT_DIR/scripts/server/check-and-start-services.sh"
else
    echo "❌ 检查脚本不存在: $PROJECT_DIR/scripts/server/check-and-start-services.sh"
    exit 1
fi
echo ""

# 3. 最终验证
echo "[3/3] 最终验证..."
echo "=========================================="
sleep 2

echo "测试 HTTPS /login:"
LOGIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/login 2>/dev/null || echo "000")
if [ "$LOGIN_CODE" = "200" ] || [ "$LOGIN_CODE" = "302" ] || [ "$LOGIN_CODE" = "401" ]; then
    echo "✅ /login 响应正常 (HTTP $LOGIN_CODE)"
else
    echo "⚠️  /login 响应异常 (HTTP $LOGIN_CODE)"
fi

echo ""
echo "测试 HTTPS /api:"
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/api/v1/health 2>/dev/null || echo "000")
if [ "$API_CODE" = "200" ] || [ "$API_CODE" = "404" ] || [ "$API_CODE" = "401" ]; then
    echo "✅ /api 响应正常 (HTTP $API_CODE)"
else
    echo "⚠️  /api 响应异常 (HTTP $API_CODE)"
fi

echo ""
echo "=========================================="
echo "✅ 所有操作完成"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查:"
echo "1. 后端服务日志: sudo journalctl -u luckyred-api -n 100 --no-pager"
echo "2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "3. 端口监听: sudo ss -tlnp | grep -E '8000|3000'"
echo ""

