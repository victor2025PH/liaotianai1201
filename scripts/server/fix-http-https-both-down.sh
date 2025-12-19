#!/bin/bash
# ============================================================
# 修复 HTTP 和 HTTPS 都无法访问的问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

echo "=========================================="
echo "🔧 修复 HTTP/HTTPS 无法访问问题"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 确保 Nginx 服务运行
echo "[1/6] 确保 Nginx 服务运行..."
echo "----------------------------------------"
if ! systemctl is-active --quiet nginx; then
    echo "启动 Nginx..."
    sudo systemctl start nginx
    sleep 2
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "❌ Nginx 服务启动失败"
    sudo systemctl status nginx --no-pager | head -10
    exit 1
fi
echo ""

# 2. 检查并修复配置文件
echo "[2/6] 检查并修复配置文件..."
echo "----------------------------------------"

# 备份当前配置
if [ -f "$NGINX_CONFIG" ]; then
    BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "备份当前配置到: $BACKUP_FILE"
    sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
fi

# 检查配置是否包含 HTTP 和 HTTPS
HAS_HTTP=$(grep -c "listen 80" "$NGINX_CONFIG" 2>/dev/null || echo "0")
HAS_HTTPS=$(grep -c "listen 443" "$NGINX_CONFIG" 2>/dev/null || echo "0")

if [ "$HAS_HTTP" -eq 0 ] || [ "$HAS_HTTPS" -eq 0 ]; then
    echo "⚠️  配置不完整，使用项目中的完整配置..."
    
    # 检查是否有 HTTPS 配置文件
    if [ -f "$PROJECT_DIR/deploy/nginx/aikz-https.conf" ]; then
        echo "使用 HTTPS 配置文件..."
        sudo cp "$PROJECT_DIR/deploy/nginx/aikz-https.conf" "$NGINX_CONFIG"
    elif [ -f "$PROJECT_DIR/deploy/nginx/aikz.conf" ]; then
        echo "使用基础配置文件（需要手动添加 HTTPS）..."
        sudo cp "$PROJECT_DIR/deploy/nginx/aikz.conf" "$NGINX_CONFIG"
    else
        echo "❌ 项目配置文件不存在"
        exit 1
    fi
else
    echo "✅ 配置文件包含 HTTP 和 HTTPS"
fi

# 确保配置文件链接存在
if [ ! -L "$NGINX_ENABLED" ] && [ ! -f "$NGINX_ENABLED" ]; then
    echo "创建配置文件链接..."
    sudo ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"
fi
echo ""

# 3. 测试 Nginx 配置
echo "[3/6] 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
    echo "✅ Nginx 配置语法正确"
else
    echo "❌ Nginx 配置有错误，请手动修复"
    echo "配置文件: $NGINX_CONFIG"
    exit 1
fi
echo ""

# 4. 检查前端和后端服务
echo "[4/6] 检查前端和后端服务..."
echo "----------------------------------------"

# 检查前端
if ! sudo ss -tlnp | grep -q ":3000 "; then
    echo "⚠️  前端服务未运行，尝试启动..."
    cd "$PROJECT_DIR/saas-demo" || exit 1
    if command -v pm2 &> /dev/null; then
        pm2 restart next-server || pm2 start npm --name next-server -- start
        sleep 3
    else
        echo "❌ PM2 未安装，无法启动前端"
    fi
fi

if sudo ss -tlnp | grep -q ":3000 "; then
    echo "✅ 前端服务正在运行"
else
    echo "❌ 前端服务启动失败"
fi

# 检查后端
if ! sudo ss -tlnp | grep -q ":8000 "; then
    echo "⚠️  后端服务未运行，尝试启动..."
    cd "$PROJECT_DIR/admin-backend" || exit 1
    if command -v pm2 &> /dev/null; then
        pm2 restart api || pm2 start ecosystem.config.js
        sleep 3
    else
        echo "❌ PM2 未安装，无法启动后端"
    fi
fi

if sudo ss -tlnp | grep -q ":8000 "; then
    echo "✅ 后端服务正在运行"
else
    echo "❌ 后端服务启动失败"
fi
echo ""

# 5. 重新加载 Nginx
echo "[5/6] 重新加载 Nginx..."
echo "----------------------------------------"
if sudo systemctl reload nginx; then
    echo "✅ Nginx 配置已重新加载"
else
    echo "⚠️  重新加载失败，尝试重启..."
    sudo systemctl restart nginx
    sleep 2
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重启"
    else
        echo "❌ Nginx 重启失败"
        exit 1
    fi
fi
echo ""

# 6. 验证服务状态
echo "[6/6] 验证服务状态..."
echo "----------------------------------------"
sleep 2

# 检查端口
if sudo ss -tlnp | grep -q ":80 "; then
    echo "✅ 端口 80 (HTTP) 正在监听"
else
    echo "❌ 端口 80 (HTTP) 未监听"
fi

if sudo ss -tlnp | grep -q ":443 "; then
    echo "✅ 端口 443 (HTTPS) 正在监听"
else
    echo "❌ 端口 443 (HTTPS) 未监听"
fi

# 测试本地连接
echo ""
echo "测试本地连接..."
if curl -s -o /dev/null -w "HTTP: %{http_code}\n" http://127.0.0.1/ | grep -q "200\|301\|302"; then
    echo "✅ HTTP 本地连接正常"
else
    echo "⚠️  HTTP 本地连接异常"
fi

if curl -s -k -o /dev/null -w "HTTPS: %{http_code}\n" https://127.0.0.1/ | grep -q "200\|301\|302"; then
    echo "✅ HTTPS 本地连接正常"
else
    echo "⚠️  HTTPS 本地连接异常"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请运行诊断脚本："
echo "  sudo bash $PROJECT_DIR/scripts/server/diagnose-http-https-down.sh"
echo ""

