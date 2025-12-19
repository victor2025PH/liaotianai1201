#!/bin/bash
# ============================================================
# 修复 502 Bad Gateway 错误
# ============================================================

echo "=========================================="
echo "🔧 修复 502 Bad Gateway 错误"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 检查 PM2 服务状态
echo "[1/7] 检查 PM2 服务状态..."
echo "----------------------------------------"
PM2_STATUS=$(sudo -u ubuntu pm2 list 2>/dev/null)
echo "$PM2_STATUS"
echo ""

# 2. 检查端口 8000 是否监听
echo "[2/7] 检查端口 8000 监听状态..."
echo "----------------------------------------"
PORT_8000=$(sudo ss -tlnp | grep ":8000" || echo "")
if [ -n "$PORT_8000" ]; then
    echo "✅ 端口 8000 正在监听:"
    echo "   $PORT_8000"
else
    echo "❌ 端口 8000 未监听"
fi
echo ""

# 3. 检查后端进程
echo "[3/7] 检查后端进程..."
echo "----------------------------------------"
BACKEND_PIDS=$(ps aux | grep -E "uvicorn|python.*app.main" | grep -v grep || echo "")
if [ -n "$BACKEND_PIDS" ]; then
    echo "✅ 发现后端进程:"
    echo "$BACKEND_PIDS"
else
    echo "❌ 未发现后端进程"
fi
echo ""

# 4. 测试直接访问后端
echo "[4/7] 测试直接访问后端..."
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
fi
echo ""

echo "测试 /docs:"
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/docs 2>/dev/null || echo "000")
if [ "$DOCS_RESPONSE" = "200" ]; then
    echo "✅ 后端文档可访问 (HTTP $DOCS_RESPONSE)"
elif [ "$DOCS_RESPONSE" = "000" ]; then
    echo "❌ 无法连接到后端 (连接被拒绝)"
else
    echo "⚠️  后端返回: HTTP $DOCS_RESPONSE"
fi
echo ""

# 5. 检查后端日志
echo "[5/7] 检查后端日志..."
echo "----------------------------------------"
echo "最近的错误日志:"
sudo -u ubuntu pm2 logs backend --lines 30 --nostream 2>&1 | grep -i "error\|failed\|exception\|traceback" | tail -10 || echo "未发现错误"
echo ""

echo "最近的启动日志:"
sudo -u ubuntu pm2 logs backend --lines 20 --nostream 2>&1 | tail -20
echo ""

# 6. 修复步骤
echo "[6/7] 执行修复..."
echo "----------------------------------------"

# 如果端口未监听或无法连接，重启后端
if [ -z "$PORT_8000" ] || [ "$HEALTH_RESPONSE" = "000" ]; then
    echo "检测到后端服务问题，正在修复..."
    
    # 停止后端
    echo "1. 停止后端服务..."
    sudo -u ubuntu pm2 stop backend 2>/dev/null || true
    sudo -u ubuntu pm2 delete backend 2>/dev/null || true
    sleep 2
    
    # 清理端口
    echo "2. 清理端口 8000..."
    sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
    sleep 2
    
    # 检查虚拟环境
    echo "3. 检查虚拟环境..."
    if [ ! -f "$BACKEND_DIR/venv/bin/uvicorn" ]; then
        echo "   虚拟环境不完整，正在重建..."
        cd "$BACKEND_DIR" || exit 1
        rm -rf venv
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip --quiet
        pip install -r requirements.txt --quiet
        echo "   ✅ 虚拟环境已重建"
    fi
    
    # 检查 .env 文件
    echo "4. 检查配置文件..."
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        echo "   创建 .env 文件..."
        if [ -f "$BACKEND_DIR/env.example" ]; then
            cp "$BACKEND_DIR/env.example" "$BACKEND_DIR/.env"
        else
            cat > "$BACKEND_DIR/.env" <<EOF
JWT_SECRET=production_secret_key_change_me
LOG_LEVEL=INFO
CORS_ORIGINS=http://aikz.usdt2026.cc,http://localhost:3000
DATABASE_URL=sqlite:///./admin.db
EOF
        fi
        echo "   ✅ .env 文件已创建"
    fi
    
    # 启动后端
    echo "5. 启动后端服务..."
    cd "$PROJECT_DIR" || exit 1
    sudo -u ubuntu pm2 start ecosystem.config.js --only backend
    echo "   ✅ 后端服务已启动"
    
    # 等待服务启动
    echo "6. 等待服务启动 (10秒)..."
    sleep 10
    
    # 验证
    echo "7. 验证服务状态..."
    sleep 3
    
    NEW_PORT=$(sudo ss -tlnp | grep ":8000" || echo "")
    NEW_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
    
    if [ -n "$NEW_PORT" ] && [ "$NEW_HEALTH" = "200" ]; then
        echo "✅ 后端服务已成功启动并监听端口 8000"
    else
        echo "❌ 后端服务启动失败"
        echo "   端口状态: $([ -n "$NEW_PORT" ] && echo "监听中" || echo "未监听")"
        echo "   健康检查: HTTP $NEW_HEALTH"
        echo "   查看详细日志: sudo -u ubuntu pm2 logs backend --lines 50"
    fi
else
    echo "✅ 后端服务运行正常，无需修复"
fi
echo ""

# 7. 重新加载 Nginx
echo "[7/7] 重新加载 Nginx..."
echo "----------------------------------------"
if sudo nginx -t 2>/dev/null; then
    sudo systemctl reload nginx
    echo "✅ Nginx 已重新加载"
    sleep 2
    
    # 测试通过 Nginx 访问
    echo "测试通过 Nginx 访问 /health:"
    NGINX_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/health 2>/dev/null || echo "000")
    if [ "$NGINX_HEALTH" = "200" ]; then
        echo "✅ 通过 Nginx 可以访问后端 (HTTP $NGINX_HEALTH)"
    else
        echo "⚠️  通过 Nginx 访问返回: HTTP $NGINX_HEALTH"
    fi
else
    echo "❌ Nginx 配置有错误"
    sudo nginx -t
fi
echo ""

# 8. 最终验证
echo "=========================================="
echo "📊 最终验证"
echo "=========================================="
echo ""

echo "PM2 服务状态:"
sudo -u ubuntu pm2 list
echo ""

echo "端口监听状态:"
sudo ss -tlnp | grep -E ":(80|8000)" || echo "未发现监听端口"
echo ""

echo "直接测试后端 /health:"
curl -s http://127.0.0.1:8000/health | head -3 || echo "无法连接"
echo ""

echo "通过 Nginx 测试 /health:"
curl -s http://127.0.0.1/health | head -3 || echo "无法连接"
echo ""

echo "通过 Nginx 测试 /api/v1:"
curl -s http://127.0.0.1/api/v1 2>&1 | head -3 || echo "无法连接"
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. 后端日志: sudo -u ubuntu pm2 logs backend --lines 100"
echo "2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "3. 后端进程: ps aux | grep uvicorn"
echo "4. 端口占用: sudo lsof -i:8000"
echo ""
