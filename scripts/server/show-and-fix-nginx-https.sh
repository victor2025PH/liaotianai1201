#!/bin/bash
# ============================================================
# 显示并修复 Nginx HTTPS 配置
# ============================================================

set +e

echo "=========================================="
echo "🔍 显示并修复 Nginx HTTPS 配置"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"

# 1. 显示完整的 HTTPS server 块
echo "[1/3] 显示 HTTPS (443) server 块配置..."
echo "=========================================="
nginx -T 2>&1 | grep -A 200 "listen.*443" | grep -A 200 "server_name.*$DOMAIN" | head -150
echo ""
echo "=========================================="
echo ""

# 2. 检查 /login 配置
echo "[2/3] 检查 /login 配置..."
echo "----------------------------------------"
LOGIN_CONFIG=$(nginx -T 2>&1 | grep -A 15 "listen.*443" | grep -A 200 "server_name.*$DOMAIN" | grep -A 10 "location.*/login")
if [ -n "$LOGIN_CONFIG" ]; then
    echo "✅ 找到 /login 配置:"
    echo "$LOGIN_CONFIG"
    if echo "$LOGIN_CONFIG" | grep -q "127.0.0.1:8000"; then
        echo "✅ /login 已正确配置为转发到后端 (8000)"
    else
        echo "❌ /login 未转发到后端 (8000)"
    fi
else
    echo "❌ 未找到 /login 配置"
fi
echo ""

# 3. 提供手动修复指南
echo "[3/3] 手动修复指南..."
echo "----------------------------------------"
echo "如果 /login 配置不存在或错误，请执行以下步骤:"
echo ""
echo "1. 编辑配置文件:"
CONFIG_FILE=$(nginx -T 2>&1 | grep "configuration file.*443" | head -1 | sed 's/# configuration file //' | sed 's/:$//')
if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE=$(find /etc/nginx -name "*.conf" | xargs grep -l "listen.*443" | head -1)
fi
echo "   sudo nano $CONFIG_FILE"
echo ""
echo "2. 找到 HTTPS server 块（包含 'listen 443' 的行）"
echo ""
echo "3. 在第一个 'location' 之前添加以下配置:"
echo ""
cat <<'EOF'
    # 登录页面 - 转发到后端（必须在根路径之前）
    location /login {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
EOF
echo ""
echo "4. 保存并测试:"
echo "   sudo nginx -t"
echo ""
echo "5. 重新加载 Nginx:"
echo "   sudo systemctl reload nginx"
echo ""
echo "6. 测试:"
echo "   curl -I https://$DOMAIN/login"
echo ""

