#!/bin/bash
# ============================================================
# 修复 API 404 问题
# ============================================================

echo "=========================================="
echo "🔧 修复 API 404 问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"

# 1. 测试直接访问后端 API
echo "[1/6] 测试直接访问后端 API..."
echo "----------------------------------------"
echo "测试 /api/v1 (根路径):"
DIRECT_API_V1=$(curl -s http://127.0.0.1:8000/api/v1 2>&1)
echo "$DIRECT_API_V1"
echo ""

echo "测试 /api/v1/notifications (列表):"
DIRECT_NOTIFICATIONS=$(curl -s http://127.0.0.1:8000/api/v1/notifications 2>&1 | head -3)
echo "$DIRECT_NOTIFICATIONS"
echo ""

echo "测试 /docs (API 文档):"
DIRECT_DOCS=$(curl -s http://127.0.0.1:8000/docs 2>&1 | grep -o "<title>.*</title>" | head -1 || echo "无法访问")
echo "$DIRECT_DOCS"
echo ""

# 2. 检查后端日志中的路由注册
echo "[2/6] 检查后端路由注册..."
echo "----------------------------------------"
echo "查看后端启动日志（查找路由注册信息）:"
sudo -u ubuntu pm2 logs backend --lines 100 --nostream 2>&1 | grep -i "route\|router\|api\|startup" | tail -20 || echo "未找到路由信息"
echo ""

# 3. 检查后端代码中的路由配置
echo "[3/6] 检查后端路由配置..."
echo "----------------------------------------"
if [ -f "$BACKEND_DIR/app/main.py" ]; then
    echo "检查 main.py 中的路由注册:"
    grep -n "include_router\|prefix=" "$BACKEND_DIR/app/main.py" | head -5
    echo ""
    
    echo "检查 API router 定义:"
    if [ -f "$BACKEND_DIR/app/api/__init__.py" ]; then
        echo "API router 文件存在"
        grep -n "APIRouter\|include_router" "$BACKEND_DIR/app/api/__init__.py" | head -10
    else
        echo "❌ API router 文件不存在"
    fi
else
    echo "❌ main.py 文件不存在"
fi
echo ""

# 4. 测试通过 Nginx 访问
echo "[4/6] 测试通过 Nginx 访问..."
echo "----------------------------------------"
echo "测试 /api/v1 (通过 Nginx):"
NGINX_API_V1=$(curl -s http://127.0.0.1/api/v1 2>&1)
echo "$NGINX_API_V1"
echo ""

echo "测试 /api/v1/notifications (通过 Nginx):"
NGINX_NOTIFICATIONS=$(curl -s http://127.0.0.1/api/v1/notifications 2>&1 | head -3)
echo "$NGINX_NOTIFICATIONS"
echo ""

# 5. 检查 Nginx 配置
echo "[5/6] 检查 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
if [ -f "$NGINX_CONFIG" ]; then
    echo "Nginx /api/ 配置:"
    grep -A 5 "location /api/" "$NGINX_CONFIG" | head -10
    echo ""
    
    echo "检查 proxy_pass 配置:"
    grep "proxy_pass.*8000" "$NGINX_CONFIG" | head -5
else
    echo "❌ Nginx 配置文件不存在"
fi
echo ""

# 6. 修复步骤
echo "[6/6] 执行修复..."
echo "----------------------------------------"

# 如果直接访问后端也返回 404，说明后端路由未注册
if echo "$DIRECT_API_V1" | grep -q "Not Found\|404"; then
    echo "❌ 后端路由未正确注册，正在重启后端服务..."
    
    # 停止后端
    sudo -u ubuntu pm2 stop backend
    sleep 2
    
    # 检查虚拟环境
    if [ ! -f "$BACKEND_DIR/venv/bin/uvicorn" ]; then
        echo "虚拟环境不完整，正在重建..."
        cd "$BACKEND_DIR" || exit 1
        rm -rf venv
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip --quiet
        pip install -r requirements.txt --quiet
        echo "✅ 虚拟环境已重建"
    fi
    
    # 重启后端
    cd "$PROJECT_DIR" || exit 1
    sudo -u ubuntu pm2 restart backend
    sleep 5
    
    # 再次测试
    echo "重新测试后端 API:"
    NEW_TEST=$(curl -s http://127.0.0.1:8000/api/v1 2>&1 | head -3)
    echo "$NEW_TEST"
    
    if echo "$NEW_TEST" | grep -q "Not Found\|404"; then
        echo "⚠️  后端路由仍然未注册，请检查后端代码"
        echo "查看后端日志: sudo -u ubuntu pm2 logs backend --lines 50"
    else
        echo "✅ 后端路由已注册"
    fi
else
    echo "✅ 后端路由正常，问题可能在 Nginx 配置"
    
    # 检查 Nginx proxy_pass 配置
    if grep -q "proxy_pass http://127.0.0.1:8000/api/;" "$NGINX_CONFIG"; then
        echo "检查 Nginx proxy_pass 配置..."
        echo "当前配置应该将 /api/v1/... 转发到 http://127.0.0.1:8000/api/v1/..."
        echo "如果仍然 404，可能是路径匹配问题"
        
        # 重新加载 Nginx
        sudo systemctl reload nginx
        echo "✅ Nginx 已重新加载"
    fi
fi
echo ""

# 7. 最终验证
echo "=========================================="
echo "📊 最终验证"
echo "=========================================="
echo ""

echo "PM2 服务状态:"
sudo -u ubuntu pm2 list
echo ""

echo "直接测试后端 /api/v1:"
curl -s http://127.0.0.1:8000/api/v1 2>&1 | head -3
echo ""

echo "通过 Nginx 测试 /api/v1:"
curl -s http://127.0.0.1/api/v1 2>&1 | head -3
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. 后端日志: sudo -u ubuntu pm2 logs backend --lines 100"
echo "2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "3. 后端路由注册: grep -r 'include_router' $BACKEND_DIR/app/"
echo ""

