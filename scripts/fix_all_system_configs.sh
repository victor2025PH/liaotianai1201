#!/bin/bash
# 修复所有系统配置问题
# 1. 修复 aikz.usdt2026.cc 端口（3003 → 3000）
# 2. 统一使用 sites-admin-frontend（端口 3007）
# 3. 确保所有 Nginx 配置正确

set -e

echo "=========================================="
echo "🔧 修复所有系统配置"
echo "=========================================="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"

# 备份配置
BACKUP_DIR="/tmp/system_config_backup_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
echo "📦 备份现有配置到: $BACKUP_DIR"
sudo cp -r "$NGINX_AVAILABLE"/* "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ 备份完成"
echo ""

# 正确的端口映射
declare -A CORRECT_PORTS=(
    ["aikz.usdt2026.cc"]="3000"      # saas-demo
    ["tgmini.usdt2026.cc"]="3001"    # tgmini20251220
    ["hongbao.usdt2026.cc"]="3002"   # hbwy20251220
    ["aizkw.usdt2026.cc"]="3003"     # aizkw20251219
)

# 1. 修复所有网站的 Nginx 配置
echo "1️⃣ 修复所有网站的 Nginx 配置"
echo "----------------------------------------"

for domain in "${!CORRECT_PORTS[@]}"; do
    port="${CORRECT_PORTS[$domain]}"
    config_file="$NGINX_AVAILABLE/$domain"
    
    echo "检查 $domain (应该使用端口 $port)..."
    
    if [ -f "$config_file" ]; then
        # 检查当前端口
        current_port=$(sudo grep -oP "proxy_pass http://127.0.0.1:\K[0-9]+" "$config_file" 2>/dev/null | head -1 || echo "")
        
        if [ "$current_port" != "$port" ] && [ -n "$current_port" ]; then
            echo "  ⚠️  发现错误端口 $current_port，修复为 $port"
            sudo sed -i.bak "s|proxy_pass http://127.0.0.1:$current_port|proxy_pass http://127.0.0.1:$port|g" "$config_file"
            sudo sed -i.bak "s|127\.0\.0\.1:$current_port|127.0.0.1:$port|g" "$config_file"
            rm -f "$config_file.bak"
            echo "  ✅ 已修复"
        elif [ "$current_port" = "$port" ]; then
            echo "  ✅ 端口配置正确 ($port)"
        else
            echo "  ⚠️  未找到端口配置"
        fi
        
        # 确保符号链接存在
        if [ ! -L "$NGINX_ENABLED/$domain" ]; then
            sudo ln -s "$config_file" "$NGINX_ENABLED/$domain"
            echo "  ✅ 已创建符号链接"
        fi
    else
        echo "  ⚠️  配置文件不存在: $config_file"
    fi
    echo ""
done

# 2. 验证 aiadmin.usdt2026.cc 配置
echo "2️⃣ 验证管理后台配置 (aiadmin.usdt2026.cc)"
echo "----------------------------------------"

ADMIN_CONFIG="$NGINX_AVAILABLE/aiadmin.usdt2026.cc"
if [ -f "$ADMIN_CONFIG" ] || [ -L "$ADMIN_CONFIG" ]; then
    echo "检查管理后台配置..."
    
    # 检查 /api/ 是否指向 8000
    if sudo grep -q "location /api/" "$ADMIN_CONFIG" && sudo grep -A 2 "location /api/" "$ADMIN_CONFIG" | grep -q "8000"; then
        echo "  ✅ /api/ → 端口 8000 (正确)"
    else
        echo "  ⚠️  /api/ 配置可能有问题"
    fi
    
    # 检查 /admin 是否指向 3007
    if sudo grep -q "location /admin" "$ADMIN_CONFIG" && sudo grep -A 2 "location /admin" "$ADMIN_CONFIG" | grep -q "3007"; then
        echo "  ✅ /admin → 端口 3007 (sites-admin-frontend, 正确)"
    else
        echo "  ⚠️  /admin 配置可能有问题"
    fi
    
    # 检查 /ai-monitor 是否指向 3006
    if sudo grep -q "location /ai-monitor" "$ADMIN_CONFIG" && sudo grep -A 2 "location /ai-monitor" "$ADMIN_CONFIG" | grep -q "3006"; then
        echo "  ✅ /ai-monitor → 端口 3006 (ai-monitor-frontend, 正确)"
    else
        echo "  ⚠️  /ai-monitor 配置可能有问题"
    fi
else
    echo "  ⚠️  管理后台配置文件不存在"
fi

echo ""

# 3. 测试 Nginx 配置
echo "3️⃣ 测试 Nginx 配置"
echo "----------------------------------------"

if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
    
    # 重新加载 Nginx
    echo ""
    echo "🔄 重新加载 Nginx..."
    if sudo systemctl is-active --quiet nginx; then
        sudo systemctl reload nginx
        echo "✅ Nginx 已重新加载"
    else
        echo "⚠️  Nginx 服务未运行，尝试启动..."
        sudo systemctl start nginx
        if sudo systemctl is-active --quiet nginx; then
            echo "✅ Nginx 已启动"
        else
            echo "❌ Nginx 启动失败"
            sudo systemctl status nginx --no-pager -l | head -20
            exit 1
        fi
    fi
else
    echo "❌ Nginx 配置语法错误:"
    sudo nginx -t
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 配置修复完成！"
echo "=========================================="
echo ""
echo "📋 正确的端口映射:"
echo "  展示网站:"
echo "    - aikz.usdt2026.cc → 端口 3000 (saas-demo)"
echo "    - tgmini.usdt2026.cc → 端口 3001"
echo "    - hongbao.usdt2026.cc → 端口 3002"
echo "    - aizkw.usdt2026.cc → 端口 3003"
echo ""
echo "  管理后台 (aiadmin.usdt2026.cc):"
echo "    - /api/ → 端口 8000 (admin-backend)"
echo "    - /admin → 端口 3007 (sites-admin-frontend)"
echo "    - /ai-monitor → 端口 3006 (ai-monitor-frontend)"
echo ""
echo "💡 备份位置: $BACKUP_DIR"
echo ""
echo "⚠️  注意: admin-frontend 和 sites-admin-frontend 是同一个服务，"
echo "   统一使用 sites-admin-frontend (端口 3007)，不再使用 admin-frontend"
echo ""

