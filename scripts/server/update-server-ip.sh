#!/bin/bash
# ============================================================
# 更新服务器IP地址配置
# ============================================================

set -e

echo "=========================================="
echo "🔧 更新服务器IP地址配置"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

NEW_IP="165.154.254.24"
DOMAIN="aikz.usdt2026.cc"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 1. 检查DNS解析
echo "[1/5] 检查DNS解析..."
echo "----------------------------------------"
CURRENT_IP=$(host "$DOMAIN" 2>/dev/null | grep "has address" | awk '{print $4}' | head -1 || echo "")

if [ -n "$CURRENT_IP" ]; then
    echo "当前域名 $DOMAIN 解析到: $CURRENT_IP"
    if [ "$CURRENT_IP" = "$NEW_IP" ]; then
        echo "✅ DNS 已正确解析到新IP"
    else
        echo "⚠️  DNS 尚未更新，当前解析到: $CURRENT_IP"
        echo "   请确保域名 $DOMAIN 的DNS记录指向: $NEW_IP"
    fi
else
    echo "⚠️  无法解析域名 $DOMAIN"
    echo "   请确保域名DNS记录指向: $NEW_IP"
fi
echo ""

# 2. 更新 master_config.json（如果有主服务器配置）
echo "[2/5] 检查 master_config.json..."
echo "----------------------------------------"
if [ -f "$PROJECT_DIR/data/master_config.json" ]; then
    echo "发现 master_config.json，检查是否需要更新..."
    # 这里不自动更新，因为这是Worker节点配置，不是主服务器
    echo "✅ master_config.json 存在（Worker节点配置，无需修改）"
else
    echo "⚠️  master_config.json 不存在"
fi
echo ""

# 3. 更新 Nginx 配置（确保使用域名而不是IP）
echo "[3/5] 检查 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-enabled/default"

if [ -f "$NGINX_CONFIG" ]; then
    # 检查是否使用了IP而不是域名
    if grep -q "server_name.*165\.154\." "$NGINX_CONFIG" || grep -q "server_name.*10\.11\." "$NGINX_CONFIG"; then
        echo "⚠️  发现Nginx配置中使用了IP地址，建议使用域名"
        echo "   当前配置:"
        grep "server_name" "$NGINX_CONFIG" | head -5
    else
        echo "✅ Nginx 配置使用域名: $DOMAIN"
    fi
else
    echo "⚠️  Nginx 配置文件不存在"
fi
echo ""

# 4. 更新环境变量（如果需要）
echo "[4/5] 检查环境变量配置..."
echo "----------------------------------------"
# 后端环境变量
if [ -f "$PROJECT_DIR/admin-backend/.env" ]; then
    # 检查 CORS_ORIGINS 是否包含旧IP
    if grep -q "CORS_ORIGINS.*165\.154\." "$PROJECT_DIR/admin-backend/.env" || \
       grep -q "CORS_ORIGINS.*10\.11\." "$PROJECT_DIR/admin-backend/.env"; then
        echo "⚠️  后端 .env 中的 CORS_ORIGINS 可能包含旧IP"
        echo "   建议检查并更新为: CORS_ORIGINS=https://${DOMAIN},http://localhost:3000"
    else
        echo "✅ 后端环境变量配置正常"
    fi
else
    echo "⚠️  后端 .env 文件不存在"
fi

# 前端环境变量
if [ -f "$PROJECT_DIR/saas-demo/.env.local" ]; then
    # 检查 API_BASE_URL 是否包含旧IP
    if grep -q "NEXT_PUBLIC_API_BASE_URL.*165\.154\." "$PROJECT_DIR/saas-demo/.env.local" || \
       grep -q "NEXT_PUBLIC_API_BASE_URL.*10\.11\." "$PROJECT_DIR/saas-demo/.env.local"; then
        echo "⚠️  前端 .env.local 中的 API_BASE_URL 可能包含旧IP"
        echo "   建议更新为: NEXT_PUBLIC_API_BASE_URL=https://${DOMAIN}/api/v1"
    else
        echo "✅ 前端环境变量配置正常"
    fi
else
    echo "⚠️  前端 .env.local 文件不存在"
fi
echo ""

# 5. 验证服务器IP
echo "[5/5] 验证服务器IP..."
echo "----------------------------------------"
# 获取当前服务器的实际IP
CURRENT_SERVER_IP=$(hostname -I | awk '{print $1}' || echo "")

if [ -n "$CURRENT_SERVER_IP" ]; then
    echo "当前服务器IP: $CURRENT_SERVER_IP"
    if [ "$CURRENT_SERVER_IP" = "$NEW_IP" ]; then
        echo "✅ 服务器IP匹配"
    else
        echo "⚠️  服务器IP不匹配"
        echo "   期望: $NEW_IP"
        echo "   实际: $CURRENT_SERVER_IP"
        echo "   如果这是新服务器，请确保这是正确的IP地址"
    fi
else
    echo "⚠️  无法获取服务器IP"
fi
echo ""

# 总结
echo "=========================================="
echo "📋 更新总结"
echo "=========================================="
echo ""
echo "新服务器IP: $NEW_IP"
echo "域名: $DOMAIN"
echo ""
echo "重要提醒:"
echo "1. 确保域名DNS记录已更新:"
echo "   $DOMAIN -> $NEW_IP"
echo ""
echo "2. 验证DNS解析:"
echo "   host $DOMAIN"
echo "   nslookup $DOMAIN"
echo ""
echo "3. 如果环境变量中包含旧IP，请手动更新:"
echo "   nano $PROJECT_DIR/admin-backend/.env"
echo "   nano $PROJECT_DIR/saas-demo/.env.local"
echo ""
echo "4. 配置SSL证书（如果DNS已更新）:"
echo "   sudo certbot --nginx -d $DOMAIN --register-unsafely-without-email"
echo ""
echo "5. 重启服务使配置生效:"
echo "   sudo systemctl restart luckyred-api"
echo "   sudo systemctl restart liaotian-frontend"
echo "   sudo systemctl restart nginx"
echo ""

