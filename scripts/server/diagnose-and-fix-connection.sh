#!/bin/bash
# ============================================================
# 全面诊断并修复网站连接问题
# ============================================================

echo "=========================================="
echo "🔍 全面诊断网站连接问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
DOMAIN="aikz.usdt2026.cc"
NGINX_AVAILABLE="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"

# 1. 检查服务状态
echo "[1/8] 检查服务状态..."
echo "----------------------------------------"
echo "PM2 服务:"
sudo -u ubuntu pm2 list 2>/dev/null || echo "PM2 未运行"
echo ""

echo "端口监听状态:"
sudo ss -tlnp | grep -E ":(80|443|3000|8000)" || echo "未发现监听端口"
echo ""

# 2. 检查 Nginx 服务状态
echo "[2/8] 检查 Nginx 服务状态..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行，正在启动..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    sleep 2
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已启动"
    else
        echo "❌ Nginx 启动失败"
        sudo systemctl status nginx --no-pager | head -10
    fi
fi
echo ""

# 3. 检查 Nginx 配置文件
echo "[3/8] 检查 Nginx 配置文件..."
echo "----------------------------------------"
if [ -f "$NGINX_AVAILABLE" ]; then
    echo "✅ 配置文件存在: $NGINX_AVAILABLE"
    echo "配置文件内容预览:"
    head -20 "$NGINX_AVAILABLE"
    echo "..."
else
    echo "❌ 配置文件不存在: $NGINX_AVAILABLE"
    echo "正在从项目目录复制配置..."
    if [ -f "$PROJECT_DIR/deploy/nginx/aikz.conf" ]; then
        sudo cp "$PROJECT_DIR/deploy/nginx/aikz.conf" "$NGINX_AVAILABLE"
        echo "✅ 配置文件已复制"
    else
        echo "❌ 项目目录中找不到配置文件"
    fi
fi
echo ""

# 4. 检查 Nginx 配置是否启用
echo "[4/8] 检查 Nginx 配置是否启用..."
echo "----------------------------------------"
if [ -L "$NGINX_ENABLED" ] || [ -f "$NGINX_ENABLED" ]; then
    echo "✅ 配置已启用: $NGINX_ENABLED"
    if [ -L "$NGINX_ENABLED" ]; then
        echo "   链接目标: $(readlink -f "$NGINX_ENABLED")"
    fi
else
    echo "❌ 配置未启用，正在创建符号链接..."
    sudo ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
    echo "✅ 符号链接已创建"
fi
echo ""

# 5. 检查 Nginx 配置语法
echo "[5/8] 检查 Nginx 配置语法..."
echo "----------------------------------------"
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    sudo nginx -t
else
    echo "❌ Nginx 配置语法错误:"
    sudo nginx -t
    echo ""
    echo "⚠️  尝试修复配置..."
    # 如果配置有错误，使用项目中的配置覆盖
    if [ -f "$PROJECT_DIR/deploy/nginx/aikz.conf" ]; then
        sudo cp "$PROJECT_DIR/deploy/nginx/aikz.conf" "$NGINX_AVAILABLE"
        sudo ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
        echo "✅ 已使用项目配置覆盖"
        sudo nginx -t
    fi
fi
echo ""

# 6. 检查防火墙
echo "[6/8] 检查防火墙状态..."
echo "----------------------------------------"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | head -1)
    echo "防火墙状态: $UFW_STATUS"
    if echo "$UFW_STATUS" | grep -q "inactive"; then
        echo "✅ 防火墙未启用（允许所有连接）"
    else
        echo "检查端口 80 和 443 是否开放:"
        sudo ufw status | grep -E "(80|443)" || echo "⚠️  端口可能未开放"
        echo ""
        echo "如果需要，运行以下命令开放端口:"
        echo "  sudo ufw allow 80/tcp"
        echo "  sudo ufw allow 443/tcp"
    fi
else
    echo "⚠️  ufw 未安装，检查 iptables..."
    sudo iptables -L -n | grep -E "(80|443)" || echo "未发现防火墙规则"
fi
echo ""

# 7. 检查 SSL 证书（如果访问 HTTPS）
echo "[7/8] 检查 SSL 证书..."
echo "----------------------------------------"
SSL_CERT="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
SSL_KEY="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"

if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    echo "✅ SSL 证书存在"
    echo "   证书: $SSL_CERT"
    echo "   私钥: $SSL_KEY"
    echo ""
    echo "⚠️  注意: 当前 Nginx 配置只监听 HTTP (端口 80)"
    echo "   如果用户访问 HTTPS，需要添加 SSL 配置"
else
    echo "ℹ️  SSL 证书不存在（这是正常的，如果只使用 HTTP）"
    echo ""
    echo "⚠️  重要: 如果用户访问 https://${DOMAIN}，会失败"
    echo "   当前配置只支持 http://${DOMAIN}"
fi
echo ""

# 8. 检查后端和前端服务
echo "[8/8] 检查后端和前端服务..."
echo "----------------------------------------"
echo "检查前端服务 (端口 3000):"
if sudo ss -tlnp | grep -q ":3000"; then
    echo "✅ 前端服务正在监听端口 3000"
    # 测试连接
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 | grep -q "200\|404\|500"; then
        echo "✅ 前端服务响应正常"
    else
        echo "⚠️  前端服务无响应"
    fi
else
    echo "❌ 前端服务未监听端口 3000"
    echo "   检查 PM2 状态:"
    sudo -u ubuntu pm2 list | grep frontend || echo "   前端服务未运行"
fi
echo ""

echo "检查后端服务 (端口 8000):"
if sudo ss -tlnp | grep -q ":8000"; then
    echo "✅ 后端服务正在监听端口 8000"
    # 测试连接
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health | grep -q "200\|404\|500"; then
        echo "✅ 后端服务响应正常"
    else
        echo "⚠️  后端服务无响应"
    fi
else
    echo "❌ 后端服务未监听端口 8000"
    echo "   检查 PM2 状态:"
    sudo -u ubuntu pm2 list | grep backend || echo "   后端服务未运行"
fi
echo ""

# 9. 重新加载 Nginx
echo "=========================================="
echo "🔄 重新加载 Nginx..."
echo "=========================================="
sudo systemctl reload nginx
sleep 2

# 10. 最终检查
echo ""
echo "=========================================="
echo "📊 最终状态检查"
echo "=========================================="
echo ""

echo "Nginx 状态:"
sudo systemctl status nginx --no-pager | head -5
echo ""

echo "端口监听:"
sudo ss -tlnp | grep -E ":(80|443|3000|8000)" || echo "未发现监听端口"
echo ""

echo "PM2 服务:"
sudo -u ubuntu pm2 list
echo ""

# 11. 测试本地连接
echo "=========================================="
echo "🧪 测试本地连接"
echo "=========================================="
echo ""

echo "测试 Nginx (端口 80):"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "000" ]; then
    echo "✅ Nginx 响应: HTTP $HTTP_CODE"
else
    echo "❌ Nginx 无响应"
fi
echo ""

echo "测试前端 (端口 3000):"
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_CODE" != "000" ]; then
    echo "✅ 前端响应: HTTP $FRONTEND_CODE"
else
    echo "❌ 前端无响应"
fi
echo ""

echo "测试后端 (端口 8000):"
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_CODE" != "000" ]; then
    echo "✅ 后端响应: HTTP $BACKEND_CODE"
else
    echo "❌ 后端无响应"
fi
echo ""

# 12. 诊断建议
echo "=========================================="
echo "💡 诊断建议"
echo "=========================================="
echo ""

if [ "$HTTP_CODE" = "000" ]; then
    echo "❌ Nginx 无法访问，可能的原因:"
    echo "   1. Nginx 未运行: sudo systemctl start nginx"
    echo "   2. 防火墙阻止: sudo ufw allow 80/tcp"
    echo "   3. 配置错误: sudo nginx -t"
fi

if [ "$FRONTEND_CODE" = "000" ]; then
    echo "❌ 前端服务无法访问，可能的原因:"
    echo "   1. 前端服务未运行: sudo -u ubuntu pm2 restart frontend"
    echo "   2. 端口被占用: sudo lsof -i:3000"
    echo "   3. 构建失败: cd $PROJECT_DIR/saas-demo && npm run build"
fi

if [ "$BACKEND_CODE" = "000" ]; then
    echo "❌ 后端服务无法访问，可能的原因:"
    echo "   1. 后端服务未运行: sudo -u ubuntu pm2 restart backend"
    echo "   2. 端口被占用: sudo lsof -i:8000"
    echo "   3. 虚拟环境问题: cd $PROJECT_DIR/admin-backend && source venv/bin/activate"
fi

echo ""
echo "如果网站仍无法访问，请检查:"
echo "1. 域名 DNS 解析是否正确指向服务器 IP"
echo "2. 云服务商安全组是否开放端口 80 和 443"
echo "3. 服务器防火墙是否允许连接"
echo "4. 如果访问 HTTPS，确保 SSL 证书已配置"
echo ""

echo "=========================================="
echo "✅ 诊断完成"
echo "=========================================="

