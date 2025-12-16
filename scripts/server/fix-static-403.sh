#!/bin/bash
# ============================================================
# Fix Static Resources 403 Forbidden (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Fix 403 Forbidden errors for Next.js static resources
#
# One-click execution: sudo bash scripts/server/fix-static-403.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 修复静态资源 403 Forbidden 错误"
echo "============================================================"
echo ""

FRONTEND_DIR="/home/ubuntu/telegram-ai-system/saas-demo"
STATIC_DIR="$FRONTEND_DIR/.next/static"
NGINX_USER="www-data"

# 检查静态资源目录
echo "[1/5] 检查静态资源目录"
echo "----------------------------------------"
if [ ! -d "$STATIC_DIR" ]; then
  echo "❌ 静态资源目录不存在: $STATIC_DIR"
  echo "请先构建前端项目"
  exit 1
fi
echo "✅ 静态资源目录存在: $STATIC_DIR"

# 检查目录结构
echo ""
echo "目录结构:"
ls -la "$STATIC_DIR" | head -10

# 修复文件权限
echo ""
echo "[2/5] 修复文件权限"
echo "----------------------------------------"
echo "设置目录所有者为 ubuntu:ubuntu..."
sudo chown -R ubuntu:ubuntu "$FRONTEND_DIR/.next" || {
  echo "⚠️  设置所有者失败，继续..."
}

echo "设置目录权限（755）..."
find "$FRONTEND_DIR/.next" -type d -exec chmod 755 {} \; || {
  echo "⚠️  设置目录权限失败，继续..."
}

echo "设置文件权限（644）..."
find "$FRONTEND_DIR/.next" -type f -exec chmod 644 {} \; || {
  echo "⚠️  设置文件权限失败，继续..."
}

echo "✅ 权限已修复"

# 检查父目录权限
echo ""
echo "[3/5] 检查父目录权限"
echo "----------------------------------------"
PARENT_DIRS=(
  "$FRONTEND_DIR"
  "$FRONTEND_DIR/.next"
  "$FRONTEND_DIR/.next/static"
)

for dir in "${PARENT_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    PERMS=$(stat -c "%a" "$dir" 2>/dev/null || echo "unknown")
    OWNER=$(stat -c "%U:%G" "$dir" 2>/dev/null || echo "unknown")
    echo "  $dir: $PERMS ($OWNER)"
    
    # 确保目录可执行（对于 Nginx 访问）
    if [ "$PERMS" != "755" ] && [ "$PERMS" != "775" ]; then
      echo "    修复权限为 755..."
      sudo chmod 755 "$dir" || echo "    ⚠️  修复失败"
    fi
  fi
done

# 检查 Nginx 配置
echo ""
echo "[4/5] 检查 Nginx 配置"
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-available/default"

if [ -f "$NGINX_CONFIG" ]; then
  # 检查是否有 _next/static 配置
  if grep -q "_next/static" "$NGINX_CONFIG"; then
    echo "✅ Nginx 配置中包含 _next/static 路径"
    
    # 检查是否使用 alias 或 root
    if grep -A 3 "_next/static" "$NGINX_CONFIG" | grep -q "alias"; then
      echo "✅ 使用 alias 指令（正确）"
    else
      echo "⚠️  未找到 alias 指令，可能需要更新配置"
    fi
  else
    echo "⚠️  Nginx 配置中未找到 _next/static 路径"
    echo "执行 Nginx 静态路径修复脚本..."
    if [ -f "$FRONTEND_DIR/../scripts/server/fix-nginx-static-paths.sh" ]; then
      bash "$FRONTEND_DIR/../scripts/server/fix-nginx-static-paths.sh" || {
        echo "⚠️  Nginx 配置修复失败"
      }
    fi
  fi
else
  echo "❌ Nginx 配置文件不存在: $NGINX_CONFIG"
fi

# 测试 Nginx 配置并重载
echo ""
echo "[5/5] 测试并重载 Nginx"
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
  sudo systemctl reload nginx
  echo "✅ Nginx 已重载"
else
  echo "❌ Nginx 配置语法错误"
  exit 1
fi

# 验证
echo ""
echo "=== 验证修复结果 ==="
sleep 2

DOMAIN="${SERVER_HOST:-aikz.usdt2026.cc}"

# 测试静态资源访问
STATIC_TEST=$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/_next/static/chunks/main.js" 2>/dev/null || echo "000")
if [ "$STATIC_TEST" = "200" ]; then
  echo "✅ 静态资源访问正常: HTTP 200"
elif [ "$STATIC_TEST" = "403" ]; then
  echo "⚠️  静态资源仍返回 403，可能需要检查 SELinux/AppArmor"
  echo ""
  echo "尝试以下命令："
  echo "  1. 检查 SELinux: getenforce (如果返回 Enforcing，需要设置上下文)"
  echo "  2. 检查 AppArmor: sudo aa-status | grep nginx"
  echo "  3. 临时禁用 SELinux: sudo setenforce 0 (仅用于测试)"
elif [ "$STATIC_TEST" = "404" ]; then
  echo "⚠️  静态资源返回 404（文件不存在，但路径已正确）"
else
  echo "⚠️  静态资源访问异常: HTTP $STATIC_TEST"
fi

# 检查文件是否可读
echo ""
echo "=== 检查文件可读性 ==="
TEST_FILE=$(find "$STATIC_DIR" -type f -name "*.js" 2>/dev/null | head -1)
if [ -n "$TEST_FILE" ]; then
  if [ -r "$TEST_FILE" ]; then
    echo "✅ 测试文件可读: $TEST_FILE"
  else
    echo "❌ 测试文件不可读: $TEST_FILE"
    echo "修复权限..."
    sudo chmod 644 "$TEST_FILE" || echo "⚠️  修复失败"
  fi
  
  # 检查 Nginx 用户是否可以读取
  if sudo -u "$NGINX_USER" test -r "$TEST_FILE" 2>/dev/null; then
    echo "✅ Nginx 用户 ($NGINX_USER) 可以读取文件"
  else
    echo "⚠️  Nginx 用户 ($NGINX_USER) 无法读取文件"
    echo "尝试添加 Nginx 用户到 ubuntu 组..."
    sudo usermod -a -G ubuntu "$NGINX_USER" 2>/dev/null || echo "⚠️  添加用户组失败"
    echo "或者设置文件组权限..."
    sudo chgrp -R "$NGINX_USER" "$STATIC_DIR" 2>/dev/null || echo "⚠️  设置组失败"
    sudo chmod -R g+r "$STATIC_DIR" 2>/dev/null || echo "⚠️  设置组读权限失败"
  fi
else
  echo "⚠️  未找到测试文件"
fi

echo ""
echo "============================================================"
echo "✅ 修复完成"
echo "============================================================"
echo ""
echo "如果问题仍然存在，请检查："
echo "  1. SELinux 状态: getenforce"
echo "  2. AppArmor 配置: sudo aa-status | grep nginx"
echo "  3. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "  4. 文件系统权限: ls -la $STATIC_DIR"

