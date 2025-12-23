#!/bin/bash
# 验证管理后台 Nginx 配置

set -e

echo "🔍 检查管理后台 Nginx 配置..."

# 1. 检查 Nginx 服务状态
echo ""
echo "1️⃣ 检查 Nginx 服务状态..."
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行"
    echo "   启动命令: sudo systemctl start nginx"
    exit 1
fi

# 2. 检查 Nginx 配置
echo ""
echo "2️⃣ 检查 Nginx 配置..."
CONFIG_FILE="/etc/nginx/sites-enabled/aiadmin.usdt2026.cc"
if [ -f "$CONFIG_FILE" ] || [ -L "$CONFIG_FILE" ]; then
    echo "✅ 配置文件存在: $CONFIG_FILE"
    
    # 检查 /admin 配置
    if grep -q "location /admin" "$CONFIG_FILE"; then
        echo "✅ /admin 路径配置存在"
        
        # 检查代理到 3007
        if grep -q "proxy_pass.*3007" "$CONFIG_FILE"; then
            echo "✅ 代理到端口 3007 配置存在"
        else
            echo "❌ 未找到代理到端口 3007 的配置"
        fi
    else
        echo "❌ /admin 路径配置不存在"
    fi
    
    # 显示相关配置
    echo ""
    echo "📋 相关配置内容:"
    grep -A 15 "location /admin" "$CONFIG_FILE" || echo "未找到 /admin 配置"
else
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    echo "   运行配置脚本: bash scripts/configure_admin_nginx.sh"
    exit 1
fi

# 3. 测试 Nginx 配置
echo ""
echo "3️⃣ 测试 Nginx 配置..."
if sudo nginx -t; then
    echo "✅ Nginx 配置测试通过"
else
    echo "❌ Nginx 配置测试失败"
    exit 1
fi

# 4. 检查端口监听
echo ""
echo "4️⃣ 检查端口监听..."
if sudo netstat -tlnp | grep -q ":80.*nginx"; then
    echo "✅ Nginx 正在监听端口 80"
else
    echo "⚠️  Nginx 未监听端口 80"
fi

if sudo netstat -tlnp | grep -q ":443.*nginx"; then
    echo "✅ Nginx 正在监听端口 443"
else
    echo "⚠️  Nginx 未监听端口 443"
fi

# 5. 测试本地访问
echo ""
echo "5️⃣ 测试本地访问..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3007 | grep -q "200\|404"; then
    echo "✅ 端口 3007 服务可访问"
else
    echo "❌ 端口 3007 服务不可访问"
fi

# 6. 测试 Nginx 代理
echo ""
echo "6️⃣ 测试 Nginx 代理..."
if curl -s -o /dev/null -w "%{http_code}" -H "Host: aiadmin.usdt2026.cc" http://127.0.0.1/admin | grep -q "200\|404\|301\|302"; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: aiadmin.usdt2026.cc" http://127.0.0.1/admin)
    echo "✅ Nginx 代理响应 (状态码: $HTTP_CODE)"
else
    echo "❌ Nginx 代理无响应"
fi

# 7. 检查域名解析
echo ""
echo "7️⃣ 检查域名解析..."
if host aiadmin.usdt2026.cc | grep -q "has address"; then
    IP=$(host aiadmin.usdt2026.cc | grep "has address" | head -1 | awk '{print $4}')
    echo "✅ 域名解析: aiadmin.usdt2026.cc -> $IP"
    
    # 检查服务器 IP
    SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "无法获取")
    echo "   服务器 IP: $SERVER_IP"
    
    if [ "$IP" = "$SERVER_IP" ]; then
        echo "✅ 域名指向正确的服务器"
    else
        echo "⚠️  域名可能未指向当前服务器"
    fi
else
    echo "⚠️  无法解析域名 aiadmin.usdt2026.cc"
fi

echo ""
echo "=========================================="
echo "✅ 检查完成！"
echo "=========================================="
echo ""
echo "💡 访问地址:"
echo "   - 本地: http://127.0.0.1:3007"
echo "   - 通过 Nginx: http://aiadmin.usdt2026.cc/admin"
echo "   - 通过 Nginx (HTTPS): https://aiadmin.usdt2026.cc/admin"
echo ""
echo "💡 如果无法访问，检查："
echo "   1. Nginx 服务是否运行: sudo systemctl status nginx"
echo "   2. 防火墙是否允许: sudo ufw status"
echo "   3. 域名 DNS 是否正确指向服务器"
echo "   4. 重新配置 Nginx: bash scripts/configure_admin_nginx.sh"

