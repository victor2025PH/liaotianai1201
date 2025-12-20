#!/bin/bash
# ============================================================
# 检查外部连接性和云服务商安全组
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"

echo "=========================================="
echo "🌐 检查外部连接性"
echo "=========================================="
echo ""

# 1. 获取服务器公网 IP
echo "[1/5] 获取服务器公网 IP..."
echo "----------------------------------------"
PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "无法获取")
echo "公网 IP: $PUBLIC_IP"
echo ""

# 2. 检查本地端口监听
echo "[2/5] 检查本地端口监听..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 未监听"
fi
echo ""

if sudo ss -tlnp | grep -q ":80 "; then
    echo "✅ 端口 80 正在监听"
else
    echo "❌ 端口 80 未监听"
fi
echo ""

# 3. 检查防火墙
echo "[3/5] 检查防火墙..."
echo "----------------------------------------"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | head -1)
    echo "防火墙状态: $UFW_STATUS"
    if sudo ufw status | grep -q "443/tcp"; then
        echo "✅ 防火墙允许 443 端口"
    else
        echo "❌ 防火墙未允许 443 端口"
        echo "   执行: sudo ufw allow 443/tcp"
    fi
else
    echo "ℹ️  ufw 未安装"
fi
echo ""

# 4. 测试本地连接
echo "[4/5] 测试本地连接..."
echo "----------------------------------------"
echo "测试 HTTP (本地):"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ HTTP 本地连接正常 (状态码: $HTTP_CODE)"
else
    echo "❌ HTTP 本地连接失败 (状态码: $HTTP_CODE)"
fi

echo ""
echo "测试 HTTPS (本地):"
HTTPS_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" https://127.0.0.1/ || echo "000")
if [ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "301" ] || [ "$HTTPS_CODE" = "302" ]; then
    echo "✅ HTTPS 本地连接正常 (状态码: $HTTPS_CODE)"
else
    echo "❌ HTTPS 本地连接失败 (状态码: $HTTPS_CODE)"
fi
echo ""

# 5. 检查云服务商安全组（提示）
echo "[5/5] 云服务商安全组检查（需要手动）..."
echo "----------------------------------------"
echo "⚠️  如果本地测试正常但外部无法访问，通常是云服务商安全组问题"
echo ""
echo "请检查以下云服务商的安全组设置："
echo ""
echo "1. 阿里云 (Alibaba Cloud):"
echo "   - 登录控制台 -> ECS -> 安全组"
echo "   - 添加入站规则：端口 443，协议 TCP，源 0.0.0.0/0"
echo ""
echo "2. 腾讯云 (Tencent Cloud):"
echo "   - 登录控制台 -> 云服务器 -> 安全组"
echo "   - 添加入站规则：端口 443，协议 TCP，源 0.0.0.0/0"
echo ""
echo "3. AWS:"
echo "   - EC2 -> Security Groups -> Inbound Rules"
echo "   - 添加规则：Port 443, Protocol TCP, Source 0.0.0.0/0"
echo ""
echo "4. 其他云服务商:"
echo "   - 查找 '安全组'、'防火墙'、'Network ACL' 等设置"
echo "   - 确保允许入站 443 端口"
echo ""

# 6. 使用外部工具测试
echo "使用外部工具测试连接..."
echo "----------------------------------------"
echo "可以在以下网站测试您的域名："
echo "  - https://www.sslshopper.com/ssl-checker.html#hostname=$DOMAIN"
echo "  - https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo "  - https://downforeveryoneorjustme.com/$DOMAIN"
echo ""

# 7. 检查 DNS 解析
echo "检查 DNS 解析..."
echo "----------------------------------------"
DNS_IP=$(dig +short $DOMAIN | head -1 || echo "")
if [ -n "$DNS_IP" ]; then
    echo "域名解析 IP: $DNS_IP"
    if [ "$DNS_IP" = "$PUBLIC_IP" ]; then
        echo "✅ DNS 解析正确，指向服务器 IP"
    else
        echo "⚠️  DNS 解析的 IP ($DNS_IP) 与服务器 IP ($PUBLIC_IP) 不一致"
        echo "   这可能导致连接问题"
    fi
else
    echo "❌ 无法解析域名"
fi
echo ""

echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
echo ""
echo "如果本地测试正常但浏览器无法访问，请："
echo "  1. 检查云服务商安全组（最重要）"
echo "  2. 清除浏览器缓存和 HSTS 设置"
echo "  3. 尝试使用无痕模式访问"
echo "  4. 检查 DNS 解析是否正确"
echo ""

