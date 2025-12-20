#!/bin/bash
# ============================================================
# 修复连接拒绝和静态资源路径问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

echo "=========================================="
echo "🔧 修复连接拒绝和静态资源路径问题"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 检查服务状态
echo "[1/6] 检查服务状态..."
echo "----------------------------------------"

# 检查 Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务未运行，启动..."
    sudo systemctl start nginx
    sleep 2
fi

# 检查后端
if sudo -u ubuntu pm2 list 2>/dev/null | grep -q "backend.*online"; then
    echo "✅ 后端服务正在运行"
else
    echo "❌ 后端服务未运行，启动..."
    cd "$PROJECT_DIR"
    sudo -u ubuntu pm2 start ecosystem.config.js --only backend 2>/dev/null || sudo -u ubuntu pm2 restart backend
    sleep 3
fi

# 检查前端
if sudo -u ubuntu pm2 list 2>/dev/null | grep -q "next-server.*online"; then
    echo "✅ 前端服务正在运行"
else
    echo "❌ 前端服务未运行，启动..."
    cd "$PROJECT_DIR"
    sudo -u ubuntu pm2 start ecosystem.config.js --only next-server 2>/dev/null || sudo -u ubuntu pm2 restart next-server
    sleep 3
fi
echo ""

# 2. 检查端口监听
echo "[2/6] 检查端口监听..."
echo "----------------------------------------"
if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
else
    echo "❌ 端口 443 未监听"
fi

if sudo ss -tlnp | grep -q ":80 "; then
    echo "✅ 端口 80 正在监听"
else
    echo "❌ 端口 80 未监听"
fi

if sudo ss -tlnp | grep -q ":3000 "; then
    echo "✅ 端口 3000 正在监听"
else
    echo "❌ 端口 3000 未监听"
fi

if sudo ss -tlnp | grep -q ":8000 "; then
    echo "✅ 端口 8000 正在监听"
else
    echo "❌ 端口 8000 未监听"
fi
echo ""

# 3. 修复 Nginx 配置顺序
echo "[3/6] 修复 Nginx 配置顺序..."
echo "----------------------------------------"

# 备份配置
BACKUP_DIR="/etc/nginx/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/aikz.usdt2026.cc.$(date +%Y%m%d_%H%M%S).conf"
sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "✅ 配置已备份到: $BACKUP_FILE"

# 使用模板文件（确保顺序正确）
if [ -f "$PROJECT_DIR/deploy/nginx/aikz-https.conf" ]; then
    echo "✅ 使用配置模板: $PROJECT_DIR/deploy/nginx/aikz-https.conf"
    sudo cp "$PROJECT_DIR/deploy/nginx/aikz-https.conf" "$NGINX_CONFIG"
    echo "✅ 配置文件已更新"
else
    echo "❌ 配置模板不存在"
    exit 1
fi
echo ""

# 4. 验证 location 块顺序
echo "[4/6] 验证 location 块顺序..."
echo "----------------------------------------"
NEXT_STATIC_LINE=$(grep -n "location /next/static" "$NGINX_CONFIG" | cut -d: -f1 | head -1 || echo "")
UNDERSCORE_NEXT_LINE=$(grep -n "location /_next/static" "$NGINX_CONFIG" | cut -d: -f1 | head -1 || echo "")

if [ -n "$NEXT_STATIC_LINE" ] && [ -n "$UNDERSCORE_NEXT_LINE" ]; then
    if [ "$NEXT_STATIC_LINE" -lt "$UNDERSCORE_NEXT_LINE" ]; then
        echo "✅ location 块顺序正确（/next/static 在 /_next/static 之前）"
    else
        echo "⚠️  location 块顺序不正确，需要调整"
        # 这里可以添加自动调整逻辑，但通常使用模板文件已经正确
    fi
else
    echo "⚠️  无法验证 location 块顺序"
fi
echo ""

# 5. 测试并重新加载 Nginx
echo "[5/6] 测试并重新加载 Nginx..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置测试成功"
    sudo systemctl reload nginx
    sleep 3
    
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重新加载"
    else
        echo "⚠️  重新加载失败，尝试重启..."
        sudo systemctl restart nginx
        sleep 3
    fi
else
    echo "❌ Nginx 配置测试失败"
    echo "恢复备份..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi
echo ""

# 6. 最终验证
echo "[6/6] 最终验证..."
echo "----------------------------------------"
sleep 2

# 检查端口
echo "检查端口监听："
if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 正在监听"
    sudo ss -tlnp | grep ":443 "
else
    echo "❌ 端口 443 仍未监听"
    echo "   查看 Nginx 错误日志："
    sudo tail -30 /var/log/nginx/error.log | grep -i "443\|ssl\|certificate" || sudo tail -30 /var/log/nginx/error.log
fi
echo ""

# 测试连接
echo "测试连接..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ || echo "000")
HTTPS_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" https://127.0.0.1/ || echo "000")

if [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅ HTTP 本地连接正常 (重定向到 HTTPS)"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "⚠️  HTTP 本地连接正常，但未重定向到 HTTPS"
else
    echo "❌ HTTP 本地连接失败 (状态码: $HTTP_CODE)"
fi

if [ "$HTTPS_CODE" = "200" ] || [ "$HTTPS_CODE" = "301" ] || [ "$HTTPS_CODE" = "302" ]; then
    echo "✅ HTTPS 本地连接正常"
else
    echo "❌ HTTPS 本地连接失败 (状态码: $HTTPS_CODE)"
fi
echo ""

# 测试静态资源路径
echo "测试静态资源路径..."
if curl -s -k -o /dev/null -w "%{http_code}" "https://127.0.0.1/next/static/chunks/main.js" 2>/dev/null | grep -q "200\|404"; then
    NEXT_STATIC_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" "https://127.0.0.1/next/static/chunks/main.js" 2>/dev/null)
    echo "   /next/static 路径响应: $NEXT_STATIC_CODE"
else
    echo "   /next/static 路径: 无法测试"
fi

if curl -s -k -o /dev/null -w "%{http_code}" "https://127.0.0.1/_next/static/chunks/main.js" 2>/dev/null | grep -q "200\|404"; then
    UNDERSCORE_STATIC_CODE=$(curl -s -k -o /dev/null -w "%{http_code}" "https://127.0.0.1/_next/static/chunks/main.js" 2>/dev/null)
    echo "   /_next/static 路径响应: $UNDERSCORE_STATIC_CODE"
else
    echo "   /_next/static 路径: 无法测试"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果外部仍无法访问，请检查："
echo "  1. 云服务器安全组是否开放 80 和 443 端口"
echo "  2. 防火墙规则: sudo ufw status"
echo "  3. Nginx 错误日志: sudo tail -f /var/log/nginx/error.log"
echo ""

