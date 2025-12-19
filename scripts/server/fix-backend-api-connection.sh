#!/bin/bash
# ============================================================
# 修复后端 API 连接问题
# ============================================================

echo "=========================================="
echo "🔧 修复后端 API 连接问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 检查后端服务状态
echo "[1/6] 检查后端服务状态..."
echo "----------------------------------------"
PM2_BACKEND_STATUS=$(sudo -u ubuntu pm2 list 2>/dev/null | grep backend || echo "")
if echo "$PM2_BACKEND_STATUS" | grep -q "online"; then
    echo "✅ PM2 后端服务显示为 online"
else
    echo "❌ PM2 后端服务未运行或状态异常"
    echo "   状态: $PM2_BACKEND_STATUS"
fi
echo ""

# 2. 检查端口 8000 是否监听
echo "[2/6] 检查端口 8000 监听状态..."
echo "----------------------------------------"
PORT_8000_LISTEN=$(sudo ss -tlnp | grep ":8000" || echo "")
if [ -n "$PORT_8000_LISTEN" ]; then
    echo "✅ 端口 8000 正在监听"
    echo "   $PORT_8000_LISTEN"
else
    echo "❌ 端口 8000 未监听"
fi
echo ""

# 3. 测试后端 API 连接
echo "[3/6] 测试后端 API 连接..."
echo "----------------------------------------"
BACKEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_RESPONSE" = "200" ] || [ "$BACKEND_RESPONSE" = "404" ]; then
    echo "✅ 后端 API 可以访问 (HTTP $BACKEND_RESPONSE)"
elif [ "$BACKEND_RESPONSE" = "000" ]; then
    echo "❌ 后端 API 无法连接 (连接被拒绝)"
else
    echo "⚠️  后端 API 返回: HTTP $BACKEND_RESPONSE"
fi
echo ""

# 4. 检查虚拟环境
echo "[4/6] 检查后端虚拟环境..."
echo "----------------------------------------"
if [ -f "$BACKEND_DIR/venv/bin/uvicorn" ]; then
    echo "✅ 虚拟环境中的 uvicorn 存在"
else
    echo "❌ 虚拟环境中的 uvicorn 不存在"
    echo "   路径: $BACKEND_DIR/venv/bin/uvicorn"
    echo "   正在检查虚拟环境..."
    if [ ! -d "$BACKEND_DIR/venv" ]; then
        echo "   ❌ 虚拟环境目录不存在，需要重建"
    else
        echo "   ⚠️  虚拟环境存在但 uvicorn 缺失"
    fi
fi
echo ""

# 5. 检查后端日志
echo "[5/6] 检查后端日志..."
echo "----------------------------------------"
if [ -f "$PROJECT_DIR/logs/backend-error.log" ]; then
    echo "最近的错误日志:"
    tail -20 "$PROJECT_DIR/logs/backend-error.log" 2>/dev/null || echo "无法读取错误日志"
else
    echo "⚠️  错误日志文件不存在"
fi
echo ""

if [ -f "$PROJECT_DIR/logs/backend-out.log" ]; then
    echo "最近的输出日志:"
    tail -10 "$PROJECT_DIR/logs/backend-out.log" 2>/dev/null || echo "无法读取输出日志"
else
    echo "⚠️  输出日志文件不存在"
fi
echo ""

# 6. 修复步骤
echo "[6/6] 执行修复..."
echo "----------------------------------------"

# 如果端口未监听或后端无法访问，尝试重启
if [ -z "$PORT_8000_LISTEN" ] || [ "$BACKEND_RESPONSE" = "000" ]; then
    echo "检测到后端服务问题，正在修复..."
    
    # 停止现有服务
    echo "1. 停止现有后端服务..."
    sudo -u ubuntu pm2 stop backend 2>/dev/null || true
    sudo -u ubuntu pm2 delete backend 2>/dev/null || true
    
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
    
    # 启动服务
    echo "5. 启动后端服务..."
    cd "$PROJECT_DIR" || exit 1
    sudo -u ubuntu pm2 start ecosystem.config.js --only backend
    sleep 5
    
    # 验证
    echo "6. 验证服务状态..."
    sleep 3
    NEW_PORT_STATUS=$(sudo ss -tlnp | grep ":8000" || echo "")
    NEW_BACKEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
    
    if [ -n "$NEW_PORT_STATUS" ] && [ "$NEW_BACKEND_RESPONSE" != "000" ]; then
        echo "✅ 后端服务已成功启动"
    else
        echo "❌ 后端服务启动失败"
        echo "   查看详细日志: sudo -u ubuntu pm2 logs backend --lines 50"
    fi
else
    echo "✅ 后端服务运行正常，无需修复"
fi
echo ""

# 7. 检查 Nginx API 代理配置
echo "=========================================="
echo "🔍 检查 Nginx API 代理配置"
echo "=========================================="
echo ""

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
    echo "检查 Nginx 配置中的 API 代理..."
    if grep -q "location /api/" "$NGINX_CONFIG"; then
        echo "✅ Nginx 配置包含 /api/ 代理"
        echo "相关配置:"
        grep -A 5 "location /api/" "$NGINX_CONFIG" | head -10
    else
        echo "❌ Nginx 配置缺少 /api/ 代理"
    fi
else
    echo "⚠️  Nginx 配置文件不存在"
fi
echo ""

# 8. 测试通过 Nginx 访问 API
echo "=========================================="
echo "🧪 测试通过 Nginx 访问 API"
echo "=========================================="
echo ""

NGINX_API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/api/health 2>/dev/null || echo "000")
if [ "$NGINX_API_RESPONSE" != "000" ]; then
    echo "✅ 通过 Nginx 可以访问 API (HTTP $NGINX_API_RESPONSE)"
else
    echo "❌ 通过 Nginx 无法访问 API"
    echo "   这可能是 Nginx 配置问题"
fi
echo ""

# 9. 最终状态
echo "=========================================="
echo "📊 最终状态"
echo "=========================================="
echo ""

echo "PM2 服务状态:"
sudo -u ubuntu pm2 list
echo ""

echo "端口监听状态:"
sudo ss -tlnp | grep -E ":(80|8000)" || echo "未发现监听端口"
echo ""

echo "直接测试后端:"
curl -s http://127.0.0.1:8000/health | head -5 || echo "无法连接"
echo ""

echo "通过 Nginx 测试 API:"
curl -s http://127.0.0.1/api/health | head -5 || echo "无法连接"
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. 后端日志: sudo -u ubuntu pm2 logs backend --lines 50"
echo "2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "3. 后端虚拟环境: ls -la $BACKEND_DIR/venv/bin/uvicorn"
echo ""

