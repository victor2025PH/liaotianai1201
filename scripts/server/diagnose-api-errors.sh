#!/bin/bash
# ============================================================
# 诊断 API 500 和 502 错误
# ============================================================

echo "=========================================="
echo "🔍 诊断 API 500 和 502 错误"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 检查 PM2 服务状态
echo "[1/6] 检查 PM2 服务状态..."
echo "----------------------------------------"
PM2_STATUS=$(sudo -u ubuntu pm2 list 2>/dev/null)
echo "$PM2_STATUS"
echo ""

# 2. 检查端口监听
echo "[2/6] 检查端口监听状态..."
echo "----------------------------------------"
echo "端口 3000 (前端):"
sudo ss -tlnp | grep ":3000" || echo "❌ 端口 3000 未监听"
echo ""

echo "端口 8000 (后端):"
sudo ss -tlnp | grep ":8000" || echo "❌ 端口 8000 未监听"
echo ""

# 3. 测试直接访问后端
echo "[3/6] 测试直接访问后端..."
echo "----------------------------------------"
echo "测试 /health:"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ 后端健康检查成功 (HTTP $HEALTH_RESPONSE)"
    curl -s http://127.0.0.1:8000/health | head -3
elif [ "$HEALTH_RESPONSE" = "000" ]; then
    echo "❌ 无法连接到后端 (连接被拒绝)"
else
    echo "⚠️  后端返回: HTTP $HEALTH_RESPONSE"
    curl -s http://127.0.0.1:8000/health | head -5
fi
echo ""

echo "测试 /api/v1/users/me (需要认证):"
USERS_ME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/users/me 2>/dev/null || echo "000")
if [ "$USERS_ME_RESPONSE" = "401" ]; then
    echo "✅ 端点存在，需要认证 (HTTP $USERS_ME_RESPONSE)"
elif [ "$USERS_ME_RESPONSE" = "500" ]; then
    echo "❌ 后端返回 500 错误"
    curl -s http://127.0.0.1:8000/api/v1/users/me | head -10
else
    echo "⚠️  后端返回: HTTP $USERS_ME_RESPONSE"
    curl -s http://127.0.0.1:8000/api/v1/users/me | head -5
fi
echo ""

echo "测试 /api/v1/workers/:"
WORKERS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/workers/ 2>/dev/null || echo "000")
if [ "$WORKERS_RESPONSE" = "401" ] || [ "$WORKERS_RESPONSE" = "200" ]; then
    echo "✅ 端点存在 (HTTP $WORKERS_RESPONSE)"
elif [ "$WORKERS_RESPONSE" = "500" ]; then
    echo "❌ 后端返回 500 错误"
    curl -s http://127.0.0.1:8000/api/v1/workers/ | head -10
else
    echo "⚠️  后端返回: HTTP $WORKERS_RESPONSE"
    curl -s http://127.0.0.1:8000/api/v1/workers/ | head -5
fi
echo ""

# 4. 检查后端日志
echo "[4/6] 检查后端日志..."
echo "----------------------------------------"
echo "最近的错误日志:"
sudo -u ubuntu pm2 logs backend --lines 50 --nostream 2>&1 | grep -i "error\|exception\|traceback\|500" | tail -20 || echo "未发现错误"
echo ""

echo "最近的启动日志:"
sudo -u ubuntu pm2 logs backend --lines 30 --nostream 2>&1 | tail -30
echo ""

# 5. 测试通过 Nginx 访问
echo "[5/6] 测试通过 Nginx 访问..."
echo "----------------------------------------"
echo "测试 /api/v1/users/me (通过 Nginx):"
NGINX_USERS_ME=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/api/v1/users/me 2>/dev/null || echo "000")
if [ "$NGINX_USERS_ME" = "401" ]; then
    echo "✅ 通过 Nginx 可以访问，需要认证 (HTTP $NGINX_USERS_ME)"
elif [ "$NGINX_USERS_ME" = "500" ]; then
    echo "❌ 通过 Nginx 返回 500 错误"
    curl -s https://aikz.usdt2026.cc/api/v1/users/me | head -10
elif [ "$NGINX_USERS_ME" = "502" ]; then
    echo "❌ 通过 Nginx 返回 502 错误（Nginx 无法连接到后端）"
    echo "   检查 Nginx 错误日志: sudo tail -20 /var/log/nginx/error.log"
else
    echo "⚠️  通过 Nginx 返回: HTTP $NGINX_USERS_ME"
    curl -s https://aikz.usdt2026.cc/api/v1/users/me | head -5
fi
echo ""

echo "测试 /api/v1/workers/ (通过 Nginx):"
NGINX_WORKERS=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/api/v1/workers/ 2>/dev/null || echo "000")
if [ "$NGINX_WORKERS" = "401" ] || [ "$NGINX_WORKERS" = "200" ]; then
    echo "✅ 通过 Nginx 可以访问 (HTTP $NGINX_WORKERS)"
elif [ "$NGINX_WORKERS" = "502" ]; then
    echo "❌ 通过 Nginx 返回 502 错误（Nginx 无法连接到后端）"
    echo "   检查 Nginx 错误日志: sudo tail -20 /var/log/nginx/error.log"
else
    echo "⚠️  通过 Nginx 返回: HTTP $NGINX_WORKERS"
    curl -s https://aikz.usdt2026.cc/api/v1/workers/ | head -5
fi
echo ""

# 6. 检查 Nginx 错误日志
echo "[6/6] 检查 Nginx 错误日志..."
echo "----------------------------------------"
echo "最近的 Nginx 错误:"
sudo tail -30 /var/log/nginx/error.log 2>/dev/null | grep -i "error\|502\|500" | tail -10 || echo "未发现错误"
echo ""

# 7. 检查后端数据库和配置
echo "=========================================="
echo "🔧 检查后端配置"
echo "=========================================="
echo ""

echo "检查 .env 文件:"
if [ -f "$BACKEND_DIR/.env" ]; then
    echo "✅ .env 文件存在"
    # 不显示敏感信息，只检查关键配置
    if grep -q "DATABASE_URL" "$BACKEND_DIR/.env"; then
        echo "✅ DATABASE_URL 已配置"
    else
        echo "⚠️  DATABASE_URL 未配置"
    fi
else
    echo "❌ .env 文件不存在"
fi
echo ""

echo "检查数据库文件:"
if [ -f "$BACKEND_DIR/admin.db" ]; then
    echo "✅ 数据库文件存在"
    DB_SIZE=$(du -h "$BACKEND_DIR/admin.db" | cut -f1)
    echo "   大小: $DB_SIZE"
else
    echo "⚠️  数据库文件不存在（如果是首次运行，这是正常的）"
fi
echo ""

# 8. 修复建议
echo "=========================================="
echo "💡 修复建议"
echo "=========================================="
echo ""

if [ "$HEALTH_RESPONSE" = "000" ]; then
    echo "❌ 后端服务未运行，请执行:"
    echo "   sudo -u ubuntu pm2 restart backend"
    echo "   sudo -u ubuntu pm2 logs backend --lines 50"
fi

if [ "$NGINX_USERS_ME" = "502" ] || [ "$NGINX_WORKERS" = "502" ]; then
    echo "❌ Nginx 502 错误，可能原因:"
    echo "   1. 后端服务未运行"
    echo "   2. 后端服务崩溃"
    echo "   3. Nginx 配置错误"
    echo ""
    echo "   请检查:"
    echo "   - 后端服务: sudo -u ubuntu pm2 list"
    echo "   - 后端日志: sudo -u ubuntu pm2 logs backend --lines 50"
    echo "   - Nginx 日志: sudo tail -50 /var/log/nginx/error.log"
fi

if [ "$USERS_ME_RESPONSE" = "500" ] || [ "$WORKERS_RESPONSE" = "500" ]; then
    echo "❌ 后端 500 错误，可能原因:"
    echo "   1. 数据库连接问题"
    echo "   2. 代码错误"
    echo "   3. 依赖缺失"
    echo ""
    echo "   请检查后端日志:"
    echo "   sudo -u ubuntu pm2 logs backend --lines 100"
fi

echo ""
echo "=========================================="
echo "✅ 诊断完成"
echo "=========================================="

