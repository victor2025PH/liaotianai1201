#!/bin/bash
# ============================================================
# 更新 Nginx 配置并重新加载
# ============================================================

echo "=========================================="
echo "🔄 更新 Nginx 配置"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
NGINX_ENABLED="/etc/nginx/sites-enabled/aikz.usdt2026.cc"

# 1. 备份现有配置
echo "[1/4] 备份现有配置..."
echo "----------------------------------------"
if [ -f "$NGINX_CONFIG" ]; then
    sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 配置已备份"
else
    echo "⚠️  配置文件不存在"
fi
echo ""

# 2. 复制新配置
echo "[2/4] 复制新配置..."
echo "----------------------------------------"
if [ -f "$PROJECT_DIR/deploy/nginx/aikz.conf" ]; then
    sudo cp "$PROJECT_DIR/deploy/nginx/aikz.conf" "$NGINX_CONFIG"
    echo "✅ 新配置已复制"
else
    echo "❌ 源配置文件不存在: $PROJECT_DIR/deploy/nginx/aikz.conf"
    exit 1
fi
echo ""

# 3. 创建符号链接（如果不存在）
echo "[3/4] 检查符号链接..."
echo "----------------------------------------"
if [ ! -L "$NGINX_ENABLED" ] && [ ! -f "$NGINX_ENABLED" ]; then
    sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
    echo "✅ 符号链接已创建"
else
    echo "✅ 符号链接已存在"
fi
echo ""

# 4. 测试并重新加载
echo "[4/4] 测试配置并重新加载..."
echo "----------------------------------------"
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    sudo nginx -t
    echo ""
    echo "重新加载 Nginx..."
    sudo systemctl reload nginx
    sleep 2
    
    if sudo systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重新加载"
    else
        echo "❌ Nginx 重新加载失败"
        sudo systemctl status nginx --no-pager | head -10
        exit 1
    fi
else
    echo "❌ Nginx 配置语法错误"
    sudo nginx -t
    echo ""
    echo "⚠️  配置有错误，已恢复备份"
    if [ -f "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)" ]; then
        LATEST_BACKUP=$(ls -t ${NGINX_CONFIG}.backup.* 2>/dev/null | head -1)
        if [ -n "$LATEST_BACKUP" ]; then
            sudo cp "$LATEST_BACKUP" "$NGINX_CONFIG"
            echo "已恢复备份配置"
        fi
    fi
    exit 1
fi
echo ""

# 5. 测试静态资源访问
echo "=========================================="
echo "🧪 测试静态资源访问"
echo "=========================================="
echo ""

# 测试一个实际的 chunk 文件
CHUNK_FILE=$(find "$PROJECT_DIR/saas-demo/.next/standalone/.next/static/chunks" -name "*.js" 2>/dev/null | head -1)
if [ -n "$CHUNK_FILE" ]; then
    CHUNK_NAME=$(basename "$CHUNK_FILE")
    echo "测试文件: $CHUNK_NAME"
    echo ""
    
    # 测试通过 Nginx 访问 /next/static（浏览器请求的路径）
    echo "测试 /next/static/chunks/$CHUNK_NAME (通过 Nginx):"
    NGINX_TEST=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/next/static/chunks/$CHUNK_NAME" 2>/dev/null || echo "000")
    if [ "$NGINX_TEST" = "200" ]; then
        echo "✅ 通过 Nginx 访问成功 (HTTP $NGINX_TEST)"
    else
        echo "❌ 通过 Nginx 访问失败: HTTP $NGINX_TEST"
        echo "   检查 Nginx 错误日志: sudo tail -20 /var/log/nginx/error.log"
    fi
    echo ""
    
    # 测试通过 Nginx 访问 /_next/static（原始路径）
    echo "测试 /_next/static/chunks/$CHUNK_NAME (通过 Nginx):"
    NGINX_UNDERSCORE_TEST=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/_next/static/chunks/$CHUNK_NAME" 2>/dev/null || echo "000")
    if [ "$NGINX_UNDERSCORE_TEST" = "200" ]; then
        echo "✅ 通过 Nginx 访问成功 (HTTP $NGINX_UNDERSCORE_TEST)"
    else
        echo "⚠️  通过 Nginx 访问返回: HTTP $NGINX_UNDERSCORE_TEST"
    fi
else
    echo "⚠️  未找到 chunk 文件进行测试"
fi
echo ""

echo "=========================================="
echo "✅ 更新完成"
echo "=========================================="
echo ""
echo "如果静态资源仍然无法访问，请检查:"
echo "1. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "2. 前端服务日志: sudo -u ubuntu pm2 logs frontend --lines 30"
echo "3. 静态文件路径: ls -la $PROJECT_DIR/saas-demo/.next/standalone/.next/static/chunks/"
echo ""

