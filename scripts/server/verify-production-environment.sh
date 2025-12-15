#!/bin/bash
# ============================================================
# 验证生产环境运行状态
# ============================================================

set +e

echo "=========================================="
echo "🔍 验证生产环境运行状态"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_SERVICE="luckyred-api"
FRONTEND_SERVICE="liaotian-frontend"

# 1. 检查 Systemd 服务状态
echo "[1/6] 检查 Systemd 服务状态..."
echo "----------------------------------------"
# 后端服务
if systemctl is-active --quiet "$BACKEND_SERVICE" 2>/dev/null; then
    echo "✅ 后端服务 ($BACKEND_SERVICE): 运行中"
    BACKEND_ACTIVE=true
else
    echo "❌ 后端服务 ($BACKEND_SERVICE): 未运行"
    BACKEND_ACTIVE=false
fi

# 前端服务
if systemctl is-active --quiet "$FRONTEND_SERVICE" 2>/dev/null; then
    echo "✅ 前端服务 ($FRONTEND_SERVICE): 运行中"
    FRONTEND_ACTIVE=true
else
    echo "❌ 前端服务 ($FRONTEND_SERVICE): 未运行"
    FRONTEND_ACTIVE=false
fi
echo ""

# 2. 检查 PM2 进程（应该没有）
echo "[2/6] 检查 PM2 进程（应该为空）..."
echo "----------------------------------------"
if command -v pm2 &> /dev/null; then
    PM2_LIST=$(pm2 list 2>/dev/null | grep -v "┌\|├\|└\|─\|│" | grep -v "^$" | grep -v "id.*name" | grep -v "No processes" || true)
    if [ -z "$PM2_LIST" ] || [ "$PM2_LIST" = "" ]; then
        echo "✅ PM2 进程列表为空（正确）"
        PM2_CLEAN=true
    else
        echo "⚠️  发现 PM2 进程（应该已删除）:"
        pm2 list
        PM2_CLEAN=false
    fi
else
    echo "✅ PM2 未安装（正确）"
    PM2_CLEAN=true
fi
echo ""

# 3. 检查端口监听
echo "[3/6] 检查端口监听..."
echo "----------------------------------------"
# 端口 8000（后端）
PORT_8000_PID=$(sudo lsof -ti:8000 2>/dev/null || true)
if [ -n "$PORT_8000_PID" ]; then
    SERVICE_PID=$(systemctl show "$BACKEND_SERVICE" -p MainPID --value 2>/dev/null || echo "")
    if [ -n "$SERVICE_PID" ] && [ "$PORT_8000_PID" = "$SERVICE_PID" ]; then
        echo "✅ 端口 8000: 由 systemd 服务管理 (PID: $PORT_8000_PID)"
        PORT_8000_OK=true
    else
        echo "⚠️  端口 8000: 被其他进程占用 (PID: $PORT_8000_PID)"
        PORT_8000_OK=false
    fi
else
    echo "❌ 端口 8000: 未监听"
    PORT_8000_OK=false
fi

# 端口 3000（前端）
PORT_3000_PID=$(sudo lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_3000_PID" ]; then
    SERVICE_PID=$(systemctl show "$FRONTEND_SERVICE" -p MainPID --value 2>/dev/null || echo "")
    if [ -n "$SERVICE_PID" ] && [ "$PORT_3000_PID" = "$SERVICE_PID" ]; then
        echo "✅ 端口 3000: 由 systemd 服务管理 (PID: $PORT_3000_PID)"
        PORT_3000_OK=true
    else
        echo "⚠️  端口 3000: 被其他进程占用 (PID: $PORT_3000_PID)"
        PORT_3000_OK=false
    fi
else
    echo "❌ 端口 3000: 未监听"
    PORT_3000_OK=false
fi
echo ""

# 4. 检查服务开机自启
echo "[4/6] 检查服务开机自启..."
echo "----------------------------------------"
if systemctl is-enabled --quiet "$BACKEND_SERVICE" 2>/dev/null; then
    echo "✅ 后端服务已设置开机自启"
    BACKEND_ENABLED=true
else
    echo "⚠️  后端服务未设置开机自启"
    BACKEND_ENABLED=false
fi

if systemctl is-enabled --quiet "$FRONTEND_SERVICE" 2>/dev/null; then
    echo "✅ 前端服务已设置开机自启"
    FRONTEND_ENABLED=true
else
    echo "⚠️  前端服务未设置开机自启"
    FRONTEND_ENABLED=false
fi
echo ""

# 5. 测试服务响应
echo "[5/6] 测试服务响应..."
echo "----------------------------------------"
# 后端健康检查
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查: HTTP 200"
    BACKEND_RESPONSE=true
else
    echo "❌ 后端健康检查: HTTP $BACKEND_HEALTH"
    BACKEND_RESPONSE=false
fi

# 前端根路径
FRONTEND_ROOT=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>/dev/null || echo "000")
if [ "$FRONTEND_ROOT" = "200" ] || [ "$FRONTEND_ROOT" = "404" ]; then
    echo "✅ 前端根路径: HTTP $FRONTEND_ROOT"
    FRONTEND_RESPONSE=true
else
    echo "❌ 前端根路径: HTTP $FRONTEND_ROOT"
    FRONTEND_RESPONSE=false
fi

# 前端登录页面
FRONTEND_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_LOGIN" = "200" ]; then
    echo "✅ 前端登录页面: HTTP 200"
    FRONTEND_LOGIN_OK=true
else
    echo "❌ 前端登录页面: HTTP $FRONTEND_LOGIN"
    FRONTEND_LOGIN_OK=false
fi
echo ""

# 6. 检查 HTTPS 访问（通过 Nginx）
echo "[6/6] 检查 HTTPS 访问（通过 Nginx）..."
echo "----------------------------------------"
HTTPS_LOGIN=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/login 2>/dev/null || echo "000")
if [ "$HTTPS_LOGIN" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
    HTTPS_OK=true
elif [ "$HTTPS_LOGIN" = "502" ]; then
    echo "❌ HTTPS /login: HTTP 502 (Bad Gateway)"
    HTTPS_OK=false
elif [ "$HTTPS_LOGIN" = "404" ]; then
    echo "⚠️  HTTPS /login: HTTP 404 (Not Found)"
    HTTPS_OK=false
else
    echo "⚠️  HTTPS /login: HTTP $HTTPS_LOGIN"
    HTTPS_OK=false
fi

HTTPS_API=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/api/v1/health 2>/dev/null || echo "000")
if [ "$HTTPS_API" = "200" ] || [ "$HTTPS_API" = "404" ] || [ "$HTTPS_API" = "401" ]; then
    echo "✅ HTTPS /api: HTTP $HTTPS_API"
    HTTPS_API_OK=true
else
    echo "❌ HTTPS /api: HTTP $HTTPS_API"
    HTTPS_API_OK=false
fi
echo ""

# 总结报告
echo "=========================================="
echo "📋 验证总结报告"
echo "=========================================="
echo ""

ALL_OK=true

# Systemd 服务
if [ "$BACKEND_ACTIVE" = true ] && [ "$FRONTEND_ACTIVE" = true ]; then
    echo "✅ Systemd 服务: 正常运行"
else
    echo "❌ Systemd 服务: 存在问题"
    ALL_OK=false
fi

# PM2 清理
if [ "$PM2_CLEAN" = true ]; then
    echo "✅ PM2 清理: 完成"
else
    echo "⚠️  PM2 清理: 未完成（仍有进程）"
    ALL_OK=false
fi

# 端口监听
if [ "$PORT_8000_OK" = true ] && [ "$PORT_3000_OK" = true ]; then
    echo "✅ 端口监听: 正常"
else
    echo "❌ 端口监听: 异常"
    ALL_OK=false
fi

# 开机自启
if [ "$BACKEND_ENABLED" = true ] && [ "$FRONTEND_ENABLED" = true ]; then
    echo "✅ 开机自启: 已配置"
else
    echo "⚠️  开机自启: 未完全配置"
    ALL_OK=false
fi

# 服务响应
if [ "$BACKEND_RESPONSE" = true ] && [ "$FRONTEND_RESPONSE" = true ] && [ "$FRONTEND_LOGIN_OK" = true ]; then
    echo "✅ 服务响应: 正常"
else
    echo "❌ 服务响应: 异常"
    ALL_OK=false
fi

# HTTPS 访问
if [ "$HTTPS_OK" = true ] && [ "$HTTPS_API_OK" = true ]; then
    echo "✅ HTTPS 访问: 正常"
else
    echo "⚠️  HTTPS 访问: 存在问题"
    ALL_OK=false
fi

echo ""

if [ "$ALL_OK" = true ]; then
    echo "✅ 所有检查通过！生产环境运行正常。"
else
    echo "⚠️  部分检查未通过，请查看上面的详细信息。"
fi

echo ""
echo "=========================================="
echo "详细服务信息"
echo "=========================================="
echo ""
echo "后端服务:"
systemctl status "$BACKEND_SERVICE" --no-pager -l | head -15
echo ""
echo "前端服务:"
systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -15
echo ""

