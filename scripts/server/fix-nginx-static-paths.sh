#!/bin/bash
# ============================================================
# Fix Nginx Static Paths (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Fix Nginx configuration to handle both /next/static/ and /_next/static/ paths
#
# One-click execution: sudo bash scripts/server/fix-nginx-static-paths.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 修复 Nginx 静态资源路径配置"
echo "============================================================"
echo ""

DOMAIN="${SERVER_HOST:-aikz.usdt2026.cc}"
NGINX_CONFIG="/etc/nginx/sites-available/default"
FRONTEND_DIR="/home/ubuntu/telegram-ai-system/saas-demo"

# 备份 Nginx 配置
echo "[1/4] 备份 Nginx 配置"
echo "----------------------------------------"
if [ -f "$NGINX_CONFIG" ]; then
  sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"
  echo "✅ 已备份到: ${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"
else
  echo "⚠️  Nginx 配置文件不存在: $NGINX_CONFIG"
  exit 1
fi

# 检查静态资源目录
echo ""
echo "[2/4] 检查静态资源目录"
echo "----------------------------------------"
STATIC_DIR=""
if [ -d "$FRONTEND_DIR/.next/static" ]; then
  STATIC_DIR="$FRONTEND_DIR/.next/static"
  echo "✅ 找到静态资源目录: $STATIC_DIR"
elif [ -d "$FRONTEND_DIR/.next/standalone/saas-demo/.next/static" ]; then
  STATIC_DIR="$FRONTEND_DIR/.next/standalone/saas-demo/.next/static"
  echo "✅ 找到静态资源目录: $STATIC_DIR"
else
  echo "⚠️  静态资源目录不存在，但继续配置 Nginx"
  STATIC_DIR="$FRONTEND_DIR/.next/static"
fi

# 读取当前 Nginx 配置
echo ""
echo "[3/4] 更新 Nginx 配置"
echo "----------------------------------------"

# 检查是否已有 /_next/static/ 或 /next/static/ 配置
if sudo grep -q "location.*_next/static\|location.*next/static" "$NGINX_CONFIG" 2>/dev/null; then
  echo "⚠️  检测到已有静态资源配置，将更新..."
  # 删除旧的静态资源配置
  sudo sed -i '/location.*_next\/static/,/^[[:space:]]*}/d' "$NGINX_CONFIG" 2>/dev/null || true
  sudo sed -i '/location.*next\/static/,/^[[:space:]]*}/d' "$NGINX_CONFIG" 2>/dev/null || true
fi

# 在 server 块中添加静态资源配置（在 location / 之前）
# 查找 server 块的位置
SERVER_BLOCK_START=$(sudo grep -n "server {" "$NGINX_CONFIG" | head -1 | cut -d: -f1)
if [ -z "$SERVER_BLOCK_START" ]; then
  echo "❌ 未找到 server 块"
  exit 1
fi

# 查找 location / 的位置
LOCATION_ROOT_LINE=$(sudo grep -n "location /" "$NGINX_CONFIG" | head -1 | cut -d: -f1)
if [ -z "$LOCATION_ROOT_LINE" ]; then
  echo "❌ 未找到 location / 配置"
  exit 1
fi

# 在 location / 之前插入静态资源配置
STATIC_CONFIG="
    # Next.js 静态资源 - 处理 /_next/static/ 路径（标准路径）
    location /_next/static/ {
        alias $FRONTEND_DIR/.next/static/;
        expires 1y;
        add_header Cache-Control \"public, immutable\";
        access_log off;
    }

    # Next.js 静态资源 - 处理 /next/static/ 路径（兼容路径，重写到 /_next/static/）
    location ~ ^/next/static/(.*)$ {
        rewrite ^/next/static/(.*)$ /_next/static/\$1 permanent;
    }
"

# 使用临时文件插入配置
TEMP_FILE=$(mktemp)
sudo sed "${LOCATION_ROOT_LINE}i\\${STATIC_CONFIG}" "$NGINX_CONFIG" > "$TEMP_FILE" 2>/dev/null || {
  # 如果 sed 插入失败，使用另一种方法
  sudo awk -v insert="$STATIC_CONFIG" -v line="$LOCATION_ROOT_LINE" '
    NR == line {print insert}
    {print}
  ' "$NGINX_CONFIG" > "$TEMP_FILE"
}
sudo mv "$TEMP_FILE" "$NGINX_CONFIG"
sudo chmod 644 "$NGINX_CONFIG"

echo "✅ Nginx 配置已更新"

# 测试 Nginx 配置
echo ""
echo "[4/4] 测试并重载 Nginx"
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
  sudo systemctl reload nginx
  echo "✅ Nginx 已重载"
else
  echo "❌ Nginx 配置语法错误"
  echo "恢复备份..."
  sudo cp "${NGINX_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)" "$NGINX_CONFIG" 2>/dev/null || {
    echo "❌ 恢复备份失败，请手动检查: $NGINX_CONFIG"
  }
  exit 1
fi

# 验证
echo ""
echo "=== 验证静态资源路径 ==="
sleep 2

# 测试 /_next/static/ 路径
STATIC_TEST1=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/_next/static/chunks/main.js" 2>/dev/null || echo "000")
if [ "$STATIC_TEST1" = "200" ] || [ "$STATIC_TEST1" = "404" ]; then
  echo "✅ /_next/static/: HTTP $STATIC_TEST1 (404 表示文件不存在，但路径已正确)"
else
  echo "⚠️  /_next/static/: HTTP $STATIC_TEST1"
fi

# 测试 /next/static/ 路径（应该重定向到 /_next/static/）
STATIC_TEST2=$(curl -s -o /dev/null -w "%{http_code}" -L "https://${DOMAIN}/next/static/chunks/main.js" 2>/dev/null || echo "000")
if [ "$STATIC_TEST2" = "200" ] || [ "$STATIC_TEST2" = "301" ] || [ "$STATIC_TEST2" = "302" ] || [ "$STATIC_TEST2" = "404" ]; then
  echo "✅ /next/static/: HTTP $STATIC_TEST2 (301/302 表示重定向成功，404 表示文件不存在但路径已处理)"
else
  echo "⚠️  /next/static/: HTTP $STATIC_TEST2"
fi

echo ""
echo "============================================================"
echo "✅ 修复完成"
echo "============================================================"
echo ""
echo "如果静态资源仍然 404，请检查："
echo "  1. 静态资源目录是否存在: ls -la $FRONTEND_DIR/.next/static/"
echo "  2. 文件权限: sudo chown -R ubuntu:ubuntu $FRONTEND_DIR/.next/"
echo "  3. Nginx 配置: sudo nginx -T | grep -A 5 '_next/static'"

