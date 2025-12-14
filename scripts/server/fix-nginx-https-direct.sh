#!/bin/bash
# ============================================================
# 直接修复 Nginx HTTPS /login 路由（简单版本）
# ============================================================

set +e

echo "=========================================="
echo "🔧 直接修复 Nginx HTTPS /login 路由"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

# 查找配置文件
CONFIG_FILE=$(nginx -T 2>&1 | grep -B 5 "listen.*443" | grep "configuration file" | head -1 | sed 's/# configuration file //' | sed 's/:$//')
if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE="/etc/nginx/sites-available/default"
fi

echo "配置文件: $CONFIG_FILE"
echo ""

# 备份
BACKUP="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP"
echo "✅ 已备份到: $BACKUP"
echo ""

# 使用 sed 直接修复
echo "修复配置..."
# 在 HTTPS server 块中，在第一个 location 之前添加 /login
sed -i '/listen.*443/,/^[[:space:]]*location[[:space:]]/ {
    /^[[:space:]]*location[[:space:]]/ {
        i\
    # 登录页面 - 转发到后端（必须在根路径之前）\
    location /login {\
        proxy_pass http://127.0.0.1:8000;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_connect_timeout 60s;\
        proxy_send_timeout 60s;\
        proxy_read_timeout 60s;\
    }\
\
    # 后端 API\
    location /api/ {\
        proxy_pass http://127.0.0.1:8000/api/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_connect_timeout 300s;\
        proxy_send_timeout 300s;\
        proxy_read_timeout 300s;\
    }\
\
' "$CONFIG_FILE"

# 测试
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ 配置语法正确"
    systemctl reload nginx
    echo "✅ Nginx 已重新加载"
else
    echo "❌ 配置错误，恢复备份"
    cp "$BACKUP" "$CONFIG_FILE"
    nginx -t
    exit 1
fi

echo ""
echo "✅ 修复完成"
echo "测试: curl -I https://aikz.usdt2026.cc/login"
echo ""

