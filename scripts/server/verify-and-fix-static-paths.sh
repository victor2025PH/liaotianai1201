#!/bin/bash
# ============================================================
# 验证并修复 Next.js 静态资源路径问题
# ============================================================

set -e

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "=========================================="
echo "🔍 验证并修复 Next.js 静态资源路径"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 检查 Nginx 配置中的静态资源路径处理
echo "[1/4] 检查 Nginx 配置..."
echo "----------------------------------------"
if grep -q "location /next/static" "$NGINX_CONFIG"; then
    echo "✅ 找到 /next/static 配置"
    echo "配置内容："
    grep -A 10 "location /next/static" "$NGINX_CONFIG" | head -12
else
    echo "❌ 未找到 /next/static 配置"
fi
echo ""

if grep -q "location /_next/static" "$NGINX_CONFIG"; then
    echo "✅ 找到 /_next/static 配置"
    echo "配置内容："
    grep -A 10 "location /_next/static" "$NGINX_CONFIG" | head -12
else
    echo "❌ 未找到 /_next/static 配置"
fi
echo ""

# 2. 测试静态资源路径
echo "[2/4] 测试静态资源路径..."
echo "----------------------------------------"

# 检查实际的静态文件
if [ -d "$FRONTEND_DIR/.next/static" ]; then
    echo "✅ 静态文件目录存在: $FRONTEND_DIR/.next/static"
    CHUNK_COUNT=$(find "$FRONTEND_DIR/.next/static/chunks" -type f 2>/dev/null | wc -l || echo "0")
    echo "   找到 $CHUNK_COUNT 个 chunk 文件"
    
    # 列出一些示例文件
    echo "   示例文件："
    find "$FRONTEND_DIR/.next/static/chunks" -type f 2>/dev/null | head -3 | while read file; do
        echo "   - $(basename "$file")"
    done
else
    echo "❌ 静态文件目录不存在: $FRONTEND_DIR/.next/static"
fi
echo ""

# 3. 测试 Nginx 重写规则
echo "[3/4] 测试 Nginx 重写规则..."
echo "----------------------------------------"

# 测试一个实际的 chunk 文件
if [ -d "$FRONTEND_DIR/.next/static/chunks" ]; then
    TEST_FILE=$(find "$FRONTEND_DIR/.next/static/chunks" -type f -name "*.js" 2>/dev/null | head -1)
    if [ -n "$TEST_FILE" ]; then
        FILE_NAME=$(basename "$TEST_FILE")
        echo "测试文件: $FILE_NAME"
        
        # 测试 /_next/static 路径（应该工作）
        echo "测试 /_next/static/chunks/$FILE_NAME:"
        HTTP_CODE_UNDERSCORE=$(curl -s -o /dev/null -w "%{http_code}" "https://127.0.0.1/_next/static/chunks/$FILE_NAME" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE_UNDERSCORE" = "200" ]; then
            echo "✅ /_next/static 路径正常 (状态码: $HTTP_CODE_UNDERSCORE)"
        else
            echo "❌ /_next/static 路径失败 (状态码: $HTTP_CODE_UNDERSCORE)"
        fi
        
        # 测试 /next/static 路径（应该重写）
        echo "测试 /next/static/chunks/$FILE_NAME:"
        HTTP_CODE_NO_UNDERSCORE=$(curl -s -o /dev/null -w "%{http_code}" "https://127.0.0.1/next/static/chunks/$FILE_NAME" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE_NO_UNDERSCORE" = "200" ]; then
            echo "✅ /next/static 路径正常 (状态码: $HTTP_CODE_NO_UNDERSCORE)"
        else
            echo "❌ /next/static 路径失败 (状态码: $HTTP_CODE_NO_UNDERSCORE)"
            echo "   可能需要修复 rewrite 规则"
        fi
    else
        echo "⚠️  未找到测试文件"
    fi
else
    echo "⚠️  无法测试，静态文件目录不存在"
fi
echo ""

# 4. 检查并修复配置
echo "[4/4] 检查并修复配置..."
echo "----------------------------------------"

# 检查 rewrite 规则是否正确
if grep -q "rewrite.*/next/static.*/_next/static" "$NGINX_CONFIG"; then
    echo "✅ rewrite 规则存在"
    REWRITE_LINE=$(grep "rewrite.*/next/static.*/_next/static" "$NGINX_CONFIG")
    echo "   规则: $REWRITE_LINE"
    
    # 检查是否使用了 break 标志
    if echo "$REWRITE_LINE" | grep -q "break"; then
        echo "✅ rewrite 规则使用了 break 标志（正确）"
    else
        echo "⚠️  rewrite 规则可能缺少 break 标志"
    fi
else
    echo "❌ rewrite 规则不存在或格式不正确"
    echo "   需要添加正确的 rewrite 规则"
fi
echo ""

# 检查 location 块的顺序
echo "检查 location 块顺序..."
NEXT_STATIC_LINE=$(grep -n "location /next/static" "$NGINX_CONFIG" | cut -d: -f1 || echo "")
UNDERSCORE_NEXT_LINE=$(grep -n "location /_next/static" "$NGINX_CONFIG" | cut -d: -f1 || echo "")

if [ -n "$NEXT_STATIC_LINE" ] && [ -n "$UNDERSCORE_NEXT_LINE" ]; then
    if [ "$NEXT_STATIC_LINE" -lt "$UNDERSCORE_NEXT_LINE" ]; then
        echo "✅ location 块顺序正确（/next/static 在 /_next/static 之前）"
    else
        echo "⚠️  location 块顺序可能有问题（/next/static 应该在 /_next/static 之前）"
    fi
fi
echo ""

# 显示完整的 /next/static location 块
echo "完整的 /next/static location 块配置："
grep -A 12 "location /next/static" "$NGINX_CONFIG" | head -13
echo ""

echo "=========================================="
echo "✅ 验证完成"
echo "=========================================="
echo ""
echo "如果仍有问题，请："
echo "  1. 清除浏览器缓存（Ctrl+Shift+Delete）"
echo "  2. 使用无痕模式访问网站"
echo "  3. 检查浏览器控制台的网络请求"
echo "  4. 查看 Nginx 错误日志: sudo tail -f /var/log/nginx/error.log"
echo ""

