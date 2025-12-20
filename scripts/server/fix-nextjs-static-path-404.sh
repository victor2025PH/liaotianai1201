#!/bin/bash
# ============================================================
# 修复 Next.js 静态资源路径 404 问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

echo "=========================================="
echo "🔧 修复 Next.js 静态资源路径 404 问题"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 备份当前配置
echo "[1/5] 备份当前配置..."
echo "----------------------------------------"
BACKUP_DIR="/etc/nginx/backups"
mkdir -p "$BACKUP_DIR"
if [ -f "$NGINX_CONFIG" ]; then
    BACKUP_FILE="$BACKUP_DIR/aikz.usdt2026.cc.$(date +%Y%m%d_%H%M%S).conf"
    sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
    echo "✅ 配置已备份到: $BACKUP_FILE"
else
    echo "❌ 配置文件不存在: $NGINX_CONFIG"
    exit 1
fi
echo ""

# 2. 检查当前配置
echo "[2/5] 检查当前配置..."
echo "----------------------------------------"
if grep -q "location /next/static" "$NGINX_CONFIG"; then
    echo "✅ 已找到 /next/static 配置"
else
    echo "⚠️  未找到 /next/static 配置，需要添加"
fi

if grep -q "location /_next/static" "$NGINX_CONFIG"; then
    echo "✅ 已找到 /_next/static 配置"
else
    echo "⚠️  未找到 /_next/static 配置，需要添加"
fi
echo ""

# 3. 修复配置 - 确保 /next/static 正确重写到 /_next/static
echo "[3/5] 修复 Nginx 配置..."
echo "----------------------------------------"

# 检查是否有 HTTPS server 块
if ! grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "❌ 配置中缺少 HTTPS server 块"
    echo "   请先运行: sudo bash scripts/server/fix-http-https-complete.sh"
    exit 1
fi

# 创建临时配置文件
TEMP_CONFIG=$(mktemp)

# 读取现有配置，在 HTTPS server 块中添加/修复静态资源路径处理
# 使用 awk 来处理配置
sudo awk '
BEGIN { in_https = 0; has_next_static = 0; has_underscore_next = 0; }
/^server {/ { 
    if (in_https) { 
        # 如果我们在 HTTPS server 块中，先添加缺失的配置
        if (!has_next_static) {
            print "    # Next.js 静态资源（兼容路径 - 必须在 /_next/static 之前）"
            print "    location /next/static {"
            print "        rewrite ^/next/static/(.*)$ /_next/static/$1 break;"
            print "        proxy_pass http://127.0.0.1:3000;"
            print "        proxy_http_version 1.1;"
            print "        proxy_set_header Host $host;"
            print "        proxy_set_header X-Real-IP $remote_addr;"
            print "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;"
            print "        proxy_set_header X-Forwarded-Proto $scheme;"
            print "        expires 365d;"
            print "        add_header Cache-Control \"public, immutable\";"
            print "        access_log off;"
            print "    }"
            print ""
        }
        if (!has_underscore_next) {
            print "    # Next.js 静态资源（标准路径）"
            print "    location /_next/static {"
            print "        proxy_pass http://127.0.0.1:3000;"
            print "        proxy_http_version 1.1;"
            print "        proxy_set_header Host $host;"
            print "        proxy_set_header X-Real-IP $remote_addr;"
            print "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;"
            print "        proxy_set_header X-Forwarded-Proto $scheme;"
            print "        expires 365d;"
            print "        add_header Cache-Control \"public, immutable\";"
            print "        access_log off;"
            print "    }"
            print ""
        }
        has_next_static = 0
        has_underscore_next = 0
    }
    print
    next
}
/listen 443/ { in_https = 1; print; next }
/^}/ { 
    if (in_https) {
        # 在 HTTPS server 块结束前，添加缺失的配置
        if (!has_next_static || !has_underscore_next) {
            if (!has_next_static) {
                print "    # Next.js 静态资源（兼容路径 - 必须在 /_next/static 之前）"
                print "    location /next/static {"
                print "        rewrite ^/next/static/(.*)$ /_next/static/$1 break;"
                print "        proxy_pass http://127.0.0.1:3000;"
                print "        proxy_http_version 1.1;"
                print "        proxy_set_header Host $host;"
                print "        proxy_set_header X-Real-IP $remote_addr;"
                print "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;"
                print "        proxy_set_header X-Forwarded-Proto $scheme;"
                print "        expires 365d;"
                print "        add_header Cache-Control \"public, immutable\";"
                print "        access_log off;"
                print "    }"
                print ""
            }
            if (!has_underscore_next) {
                print "    # Next.js 静态资源（标准路径）"
                print "    location /_next/static {"
                print "        proxy_pass http://127.0.0.1:3000;"
                print "        proxy_http_version 1.1;"
                print "        proxy_set_header Host $host;"
                print "        proxy_set_header X-Real-IP $remote_addr;"
                print "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;"
                print "        proxy_set_header X-Forwarded-Proto $scheme;"
                print "        expires 365d;"
                print "        add_header Cache-Control \"public, immutable\";"
                print "        access_log off;"
                print "    }"
                print ""
            }
        }
        in_https = 0
        has_next_static = 0
        has_underscore_next = 0
    }
    print
    next
}
/location \/next\/static/ { has_next_static = 1; print; next }
/location \/_next\/static/ { has_underscore_next = 1; print; next }
{ print }
' "$NGINX_CONFIG" > "$TEMP_CONFIG"

# 更简单的方法：直接使用模板文件并确保包含正确的配置
if [ -f "$PROJECT_DIR/deploy/nginx/aikz-https.conf" ]; then
    echo "✅ 使用配置模板确保包含正确的静态资源路径处理"
    sudo cp "$PROJECT_DIR/deploy/nginx/aikz-https.conf" "$NGINX_CONFIG"
else
    # 如果模板不存在，手动添加配置
    echo "⚠️  配置模板不存在，手动添加配置..."
    
    # 检查并添加 /next/static 配置（在 /_next/static 之前）
    if ! grep -q "location /next/static" "$NGINX_CONFIG"; then
        # 在 location /_next/static 之前插入
        sudo sed -i '/location \/_next\/static/i\
    # Next.js 静态资源（兼容路径 - 必须在 /_next/static 之前）\
    location /next/static {\
        rewrite ^/next/static/(.*)$ /_next/static/$1 break;\
        proxy_pass http://127.0.0.1:3000;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        expires 365d;\
        add_header Cache-Control "public, immutable";\
        access_log off;\
    }\
' "$NGINX_CONFIG"
    fi
fi

echo "✅ 配置已更新"
echo ""

# 4. 测试配置
echo "[4/5] 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置测试成功"
else
    echo "❌ Nginx 配置测试失败"
    echo "恢复备份..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi
echo ""

# 5. 重新加载 Nginx
echo "[5/5] 重新加载 Nginx..."
echo "----------------------------------------"
sudo systemctl reload nginx
sleep 2

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 已重新加载"
else
    echo "❌ Nginx 重新加载失败"
    sudo systemctl status nginx --no-pager | head -20
    exit 1
fi
echo ""

# 验证
echo "验证静态资源路径..."
echo "----------------------------------------"
echo "测试 /next/static 路径（应该重写到 /_next/static）:"
curl -s -o /dev/null -w "状态码: %{http_code}\n" https://127.0.0.1/next/static/chunks/main.js 2>/dev/null || echo "无法测试（可能需要实际文件）"

echo ""
echo "测试 /_next/static 路径:"
curl -s -o /dev/null -w "状态码: %{http_code}\n" https://127.0.0.1/_next/static/chunks/main.js 2>/dev/null || echo "无法测试（可能需要实际文件）"
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "请清除浏览器缓存后重新访问网站"
echo ""

