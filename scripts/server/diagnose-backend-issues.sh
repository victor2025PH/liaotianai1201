#!/bin/bash
# ============================================================
# 诊断后端服务问题
# ============================================================

set +e

echo "=========================================="
echo "🔍 诊断后端服务问题"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

BACKEND_SERVICE="luckyred-api"
BACKEND_PORT=8000

# 1. 检查 systemd 服务状态
echo "[1/6] 检查 systemd 服务状态..."
echo "----------------------------------------"
systemctl status "$BACKEND_SERVICE" --no-pager -l | head -20
echo ""

# 2. 检查端口占用
echo "[2/6] 检查端口 $BACKEND_PORT 占用情况..."
echo "----------------------------------------"
PORT_PID=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
if [ -n "$PORT_PID" ]; then
    echo "端口 $BACKEND_PORT 被进程占用: PID $PORT_PID"
    echo "进程信息:"
    ps -fp $PORT_PID 2>/dev/null | head -5
    echo ""
    
    # 检查是否是 systemd 服务
    SERVICE_PID=$(systemctl show "$BACKEND_SERVICE" -p MainPID --value 2>/dev/null || echo "")
    if [ -n "$SERVICE_PID" ] && [ "$PORT_PID" = "$SERVICE_PID" ]; then
        echo "✅ 端口由 systemd 服务管理"
    else
        echo "⚠️  端口被其他进程占用（不是 systemd 服务）"
        echo "进程命令:"
        ps -fp $PORT_PID -o cmd= 2>/dev/null
    fi
else
    echo "❌ 端口 $BACKEND_PORT 未被占用"
fi
echo ""

# 3. 检查后端服务日志
echo "[3/6] 检查后端服务日志（最近50行）..."
echo "----------------------------------------"
journalctl -u "$BACKEND_SERVICE" -n 50 --no-pager | tail -30
echo ""

# 4. 测试本地连接
echo "[4/6] 测试本地连接..."
echo "----------------------------------------"
# 测试健康检查
HEALTH_RESPONSE=$(curl -s http://127.0.0.1:$BACKEND_PORT/health 2>&1)
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/health 2>/dev/null || echo "000")
echo "健康检查响应 (HTTP $HEALTH_CODE):"
echo "$HEALTH_RESPONSE" | head -5
echo ""

# 测试 /login 路由
LOGIN_RESPONSE=$(curl -s http://127.0.0.1:$BACKEND_PORT/login 2>&1)
LOGIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/login 2>/dev/null || echo "000")
echo "登录路由响应 (HTTP $LOGIN_CODE):"
echo "$LOGIN_RESPONSE" | head -5
echo ""

# 5. 检查后端路由
echo "[5/6] 检查后端路由配置..."
echo "----------------------------------------"
# 尝试访问 API 文档
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/docs 2>/dev/null || echo "000")
if [ "$DOCS_CODE" = "200" ]; then
    echo "✅ API 文档可访问 (HTTP 200)"
    echo "   访问: http://127.0.0.1:$BACKEND_PORT/docs"
else
    echo "⚠️  API 文档不可访问 (HTTP $DOCS_CODE)"
fi

# 尝试访问 OpenAPI
OPENAPI_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$BACKEND_PORT/openapi.json 2>/dev/null || echo "000")
if [ "$OPENAPI_CODE" = "200" ]; then
    echo "✅ OpenAPI 可访问 (HTTP 200)"
    echo "   可以查看所有可用路由"
else
    echo "⚠️  OpenAPI 不可访问 (HTTP $OPENAPI_CODE)"
fi
echo ""

# 6. 检查 Nginx 错误日志
echo "[6/6] 检查 Nginx 错误日志（最近20行）..."
echo "----------------------------------------"
tail -20 /var/log/nginx/error.log | grep -iE "502|upstream|connect|8000" | tail -10
echo ""

echo "=========================================="
echo "📋 诊断总结"
echo "=========================================="
echo ""

# 总结问题
ISSUES=0

if [ "$HEALTH_CODE" != "200" ] && [ "$HEALTH_CODE" != "404" ] && [ "$HEALTH_CODE" != "405" ]; then
    echo "❌ 问题 1: 后端服务无法响应 (HTTP $HEALTH_CODE)"
    echo "   可能原因: 服务未完全启动、崩溃、或端口被其他进程占用"
    ISSUES=$((ISSUES+1))
fi

if [ "$LOGIN_CODE" = "404" ]; then
    echo "⚠️  问题 2: /login 路由返回 404"
    echo "   可能原因: 后端没有 /login 路由，或路由路径不正确"
    echo "   解决方案: 检查后端路由配置，确保有 /login 或 /api/v1/auth/login 路由"
    ISSUES=$((ISSUES+1))
fi

if [ -z "$PORT_PID" ]; then
    echo "❌ 问题 3: 端口 $BACKEND_PORT 未被占用"
    echo "   解决方案: sudo systemctl start $BACKEND_SERVICE"
    ISSUES=$((ISSUES+1))
fi

if [ "$ISSUES" -eq 0 ]; then
    echo "✅ 未发现明显问题"
    echo ""
    echo "如果仍然出现 502/404 错误，请检查:"
    echo "1. Nginx 配置中的 proxy_pass 地址是否正确"
    echo "2. 后端服务是否完全启动（查看完整日志）"
    echo "3. 防火墙是否阻止了连接"
else
    echo ""
    echo "发现 $ISSUES 个问题，建议先解决这些问题"
fi

echo ""

