#!/bin/bash
# ============================================================
# 修复 Nginx 路由配置脚本
# 确保 /login 和 /api 路径正确转发到后端 (8000)
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔧 修复 Nginx 路由配置"
echo "=========================================="
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "此脚本需要 root 权限，请使用 sudo 运行"
    echo "使用方法: sudo bash $0"
    exit 1
fi

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/$DOMAIN"
NGINX_ENABLED="/etc/nginx/sites-enabled/$DOMAIN"

# 1. 检查 Nginx 配置文件
echo "[1/5] 检查 Nginx 配置文件..."
echo "----------------------------------------"
if [ ! -f "$NGINX_CONFIG" ]; then
    echo "❌ 配置文件不存在: $NGINX_CONFIG"
    echo "查找其他配置文件..."
    NGINX_CONFIG=$(find /etc/nginx -name "*$DOMAIN*" -o -name "default" | head -1)
    if [ -z "$NGINX_CONFIG" ] || [ ! -f "$NGINX_CONFIG" ]; then
        echo "❌ 未找到 Nginx 配置文件"
        exit 1
    fi
    echo "✅ 找到配置文件: $NGINX_CONFIG"
else
    echo "✅ 配置文件存在: $NGINX_CONFIG"
fi
echo ""

# 2. 备份当前配置
echo "[2/5] 备份当前配置..."
echo "----------------------------------------"
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "✅ 配置已备份到: $BACKUP_FILE"
echo ""

# 3. 检查当前配置
echo "[3/5] 检查当前配置..."
echo "----------------------------------------"
echo "检查 /login 路径配置:"
if grep -q "location.*/login" "$NGINX_CONFIG"; then
    echo "✅ 找到 /login 配置"
    grep -A 5 "location.*/login" "$NGINX_CONFIG" | head -10
else
    echo "⚠️  未找到 /login 配置"
fi
echo ""

echo "检查 /api 路径配置:"
if grep -q "location.*/api" "$NGINX_CONFIG"; then
    echo "✅ 找到 /api 配置"
    grep -A 5 "location.*/api" "$NGINX_CONFIG" | head -10
else
    echo "⚠️  未找到 /api 配置"
fi
echo ""

echo "检查根路径配置:"
if grep -q "location /" "$NGINX_CONFIG"; then
    echo "✅ 找到根路径配置"
    grep -A 3 "location /" "$NGINX_CONFIG" | head -5
    PROXY_PASS=$(grep -A 3 "location /" "$NGINX_CONFIG" | grep "proxy_pass" | head -1)
    if echo "$PROXY_PASS" | grep -q "127.0.0.1:3000"; then
        echo "⚠️  根路径转发到前端 (3000)，这可能导致 /login 也被转发到前端"
    fi
fi
echo ""

# 4. 修复配置（如果需要）
echo "[4/5] 修复配置..."
echo "----------------------------------------"
NEEDS_FIX=false

# 检查 /login 是否被转发到前端
if grep -A 10 "location /" "$NGINX_CONFIG" | grep -q "proxy_pass.*3000" && ! grep -q "location.*/login" "$NGINX_CONFIG"; then
    echo "⚠️  发现 /login 可能被转发到前端，需要添加 /login 路由"
    NEEDS_FIX=true
fi

# 检查 /api 是否被转发到后端
if ! grep -A 5 "location.*/api" "$NGINX_CONFIG" | grep -q "proxy_pass.*8000"; then
    echo "⚠️  发现 /api 可能未正确转发到后端，需要修复"
    NEEDS_FIX=true
fi

if [ "$NEEDS_FIX" = false ]; then
    echo "✅ 配置看起来正确，无需修复"
else
    echo "开始修复配置..."
    
    # 创建修复后的配置
    TEMP_CONFIG=$(mktemp)
    
    # 读取原配置并修复
    python3 <<EOF
import re
import sys

with open("$NGINX_CONFIG", "r", encoding="utf-8") as f:
    content = f.read()

# 检查是否已有 /login 配置
has_login_location = re.search(r'location\s+.*/login', content)

# 检查是否已有 /api 配置
has_api_location = re.search(r'location\s+/api', content)

# 如果根路径转发到 3000，且没有 /login 配置，需要添加
if re.search(r'location\s+/\s*\{[^}]*proxy_pass[^}]*127\.0\.0\.1:3000', content, re.DOTALL) and not has_login_location:
    # 在根路径之前插入 /login 配置
    login_config = '''
    # 登录页面 - 转发到后端
    location /login {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
'''
    # 在 location / 之前插入
    content = re.sub(
        r'(location\s+/\s*\{)',
        login_config + r'\1',
        content,
        count=1
    )
    print("✅ 已添加 /login 路由配置")

# 确保 /api 转发到后端
if has_api_location:
    # 修复现有的 /api 配置
    content = re.sub(
        r'(location\s+/api[^{]*\{[^}]*proxy_pass\s+)(http://[^;]+)',
        r'\1http://127.0.0.1:8000/api/',
        content,
        flags=re.DOTALL
    )
    print("✅ 已修复 /api 路由配置")
else:
    # 添加 /api 配置（在根路径之前）
    api_config = '''
    # 后端 API - 转发到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
'''
    content = re.sub(
        r'(location\s+/\s*\{)',
        api_config + r'\1',
        content,
        count=1
    )
    print("✅ 已添加 /api 路由配置")

with open("$TEMP_CONFIG", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 配置已修复")
EOF

    if [ -f "$TEMP_CONFIG" ]; then
        mv "$TEMP_CONFIG" "$NGINX_CONFIG"
        echo "✅ 配置已更新"
    else
        echo "❌ 配置修复失败"
        exit 1
    fi
fi
echo ""

# 5. 测试并重新加载 Nginx
echo "[5/5] 测试并重新加载 Nginx..."
echo "----------------------------------------"
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    systemctl reload nginx 2>/dev/null || systemctl restart nginx
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重新加载"
    else
        echo "❌ Nginx 重新加载失败"
        exit 1
    fi
else
    echo "❌ Nginx 配置语法错误:"
    nginx -t 2>&1 | tail -10
    echo ""
    echo "恢复备份配置..."
    cp "$BACKUP_FILE" "$NGINX_CONFIG"
    nginx -t
    exit 1
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "配置摘要:"
echo "- /login -> http://127.0.0.1:8000"
echo "- /api/ -> http://127.0.0.1:8000/api/"
echo "- / -> http://127.0.0.1:3000 (前端)"
echo ""
echo "如果仍有问题，请检查:"
echo "1. 后端服务是否运行: sudo systemctl status luckyred-api"
echo "2. 端口 8000 是否监听: sudo ss -tlnp | grep 8000"
echo "3. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo ""

