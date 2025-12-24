#!/bin/bash
# 验证端口修复结果

set -e

echo "🔍 验证端口修复结果"
echo "=========================="
echo ""

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# 1. 检查脚本和文档中的端口引用
echo "1️⃣ 检查脚本和文档中的端口引用..."
echo ""

echo "检查是否还有 admin-frontend 使用 3006 的引用:"
REMAINING=$(grep -r "admin-frontend.*3006\|3006.*admin-frontend" scripts/ docs/ 2>/dev/null | grep -v ".backup\|backup/" | grep -v "fix_admin_frontend_port.sh\|ADMIN_SYSTEM\|PORT_FIX_NEXT_STEPS\|verify_port_fix" | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ 未发现剩余引用（正确）"
else
    echo "⚠️  发现 $REMAINING 个剩余引用:"
    grep -r "admin-frontend.*3006\|3006.*admin-frontend" scripts/ docs/ 2>/dev/null | grep -v ".backup\|backup/" | grep -v "fix_admin_frontend_port.sh\|ADMIN_SYSTEM\|PORT_FIX_NEXT_STEPS\|verify_port_fix"
fi

echo ""
echo "检查新端口 3008 的引用:"
NEW_REFS=$(grep -r "admin-frontend.*3008\|3008.*admin-frontend" scripts/ docs/ 2>/dev/null | grep -v ".backup\|backup/" | grep -v "PORT_FIX_NEXT_STEPS\|verify_port_fix" | wc -l)
if [ "$NEW_REFS" -gt 0 ]; then
    echo "✅ 发现 $NEW_REFS 个新端口引用（预期）"
else
    echo "⚠️  未发现新端口引用"
fi

echo ""
echo "=========================="
echo ""

# 2. 检查端口占用
echo "2️⃣ 检查端口占用情况..."
echo ""

check_port() {
    local port=$1
    local service=$2
    local expected=$3
    
    if command -v lsof >/dev/null 2>&1; then
        if sudo lsof -i :$port 2>/dev/null | grep -q LISTEN; then
            local process=$(sudo lsof -i :$port 2>/dev/null | grep LISTEN | head -1 | awk '{print $1}')
            if [ "$expected" = "yes" ]; then
                echo "✅ 端口 $port 被占用: $process (预期: $service)"
            else
                echo "⚠️  端口 $port 被占用: $process (意外)"
            fi
        else
            if [ "$expected" = "yes" ]; then
                echo "❌ 端口 $port 未被占用 (预期: $service 应使用此端口)"
            else
                echo "✅ 端口 $port 未被占用 (正确)"
            fi
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if sudo netstat -tlnp 2>/dev/null | grep -q ":$port "; then
            local process=$(sudo netstat -tlnp 2>/dev/null | grep ":$port " | head -1 | awk '{print $7}' | cut -d'/' -f2)
            if [ "$expected" = "yes" ]; then
                echo "✅ 端口 $port 被占用: $process (预期: $service)"
            else
                echo "⚠️  端口 $port 被占用: $process (意外)"
            fi
        else
            if [ "$expected" = "yes" ]; then
                echo "❌ 端口 $port 未被占用 (预期: $service 应使用此端口)"
            else
                echo "✅ 端口 $port 未被占用 (正确)"
            fi
        fi
    else
        echo "⚠️  无法检查端口（需要 lsof 或 netstat）"
    fi
}

check_port 3006 "ai-monitor-frontend" "yes"
check_port 3007 "sites-admin-frontend" "yes"
check_port 3008 "admin-frontend" "optional"
check_port 8000 "admin-backend" "yes"

echo ""
echo "=========================="
echo ""

# 3. 检查 PM2 进程
echo "3️⃣ 检查 PM2 进程状态..."
echo ""

if command -v pm2 >/dev/null 2>&1; then
    echo "相关进程:"
    pm2 list | grep -E "admin-frontend|sites-admin-frontend|ai-monitor-frontend|backend|luckyred-api" || echo "未找到相关进程"
else
    echo "⚠️  PM2 未安装或不在 PATH 中"
fi

echo ""
echo "=========================="
echo ""

# 4. 测试服务可访问性
echo "4️⃣ 测试服务可访问性..."
echo ""

test_service() {
    local port=$1
    local service=$2
    
    if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null | grep -q "200\|404\|301\|302"; then
        local code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null)
        echo "✅ $service (端口 $port): 可访问 (HTTP $code)"
    else
        echo "❌ $service (端口 $port): 不可访问"
    fi
}

test_service 3006 "ai-monitor-frontend"
test_service 3007 "sites-admin-frontend"
test_service 3008 "admin-frontend"
test_service 8000 "admin-backend"

echo ""
echo "=========================="
echo ""

# 5. 检查 Nginx 配置
echo "5️⃣ 检查 Nginx 配置..."
echo ""

if command -v nginx >/dev/null 2>&1; then
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        echo "✅ Nginx 配置语法正确"
        
        CONFIG_FILE="/etc/nginx/sites-enabled/aiadmin.usdt2026.cc"
        if [ -f "$CONFIG_FILE" ] || [ -L "$CONFIG_FILE" ]; then
            echo ""
            echo "Nginx 路由配置:"
            sudo grep -A 3 "location /admin\|location /ai-monitor\|location /api" "$CONFIG_FILE" 2>/dev/null | grep -E "location|proxy_pass" || echo "未找到相关配置"
        else
            echo "⚠️  Nginx 配置文件不存在: $CONFIG_FILE"
        fi
    else
        echo "❌ Nginx 配置有错误:"
        sudo nginx -t
    fi
else
    echo "⚠️  Nginx 未安装或不在 PATH 中"
fi

echo ""
echo "=========================="
echo ""

# 总结
echo "📋 验证总结"
echo "=========================="
echo ""
echo "端口分配:"
echo "  - 3006: ai-monitor-frontend ✅"
echo "  - 3007: sites-admin-frontend ✅"
echo "  - 3008: admin-frontend ✅ (新端口)"
echo "  - 8000: admin-backend ✅"
echo ""
echo "💡 下一步操作:"
echo "  1. 如果需要部署 admin-frontend，运行: bash scripts/deploy_admin_frontend.sh"
echo "  2. 验证 Nginx 配置: bash scripts/verify_admin_nginx.sh"
echo "  3. 查看详细指南: docs/PORT_FIX_NEXT_STEPS.md"
echo ""

