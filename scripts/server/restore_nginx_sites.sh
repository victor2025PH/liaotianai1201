#!/bin/bash

# 恢复 Nginx 站点配置脚本
# 使用方法: bash scripts/server/restore_nginx_sites.sh

set -e

echo "=========================================="
echo "🔧 恢复 Nginx 站点配置"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 1. 清理默认配置
echo "1. 清理默认配置..."
echo "----------------------------------------"
if [ -f "/etc/nginx/sites-enabled/default" ]; then
  echo "删除 /etc/nginx/sites-enabled/default..."
  sudo rm -f /etc/nginx/sites-enabled/default
  echo "✅ 默认配置已删除"
elif [ -L "/etc/nginx/sites-enabled/default" ]; then
  echo "删除默认配置软链接..."
  sudo rm -f /etc/nginx/sites-enabled/default
  echo "✅ 默认配置软链接已删除"
else
  echo "✅ 默认配置不存在，跳过"
fi
echo ""

# 2. 检查并重新启用站点配置
echo "2. 检查并重新启用站点配置..."
echo "----------------------------------------"

SITES_AVAILABLE_DIR="/etc/nginx/sites-available"
SITES_ENABLED_DIR="/etc/nginx/sites-enabled"

# 确保目录存在
if [ ! -d "$SITES_AVAILABLE_DIR" ]; then
  echo "❌ sites-available 目录不存在: $SITES_AVAILABLE_DIR"
  exit 1
fi

if [ ! -d "$SITES_ENABLED_DIR" ]; then
  echo "创建 sites-enabled 目录..."
  sudo mkdir -p "$SITES_ENABLED_DIR"
fi

# 需要启用的站点列表
SITES=(
  "aizkw.usdt2026.cc"
  "tgmini.usdt2026.cc"
  "hongbao.usdt2026.cc"
)

ENABLED_COUNT=0

for SITE in "${SITES[@]}"; do
  SITE_FILE="$SITES_AVAILABLE_DIR/$SITE"
  ENABLED_LINK="$SITES_ENABLED_DIR/$SITE"
  
  if [ -f "$SITE_FILE" ]; then
    echo "找到站点配置: $SITE"
    
    # 删除旧的软链接（如果存在）
    if [ -L "$ENABLED_LINK" ] || [ -f "$ENABLED_LINK" ]; then
      echo "  删除旧链接: $ENABLED_LINK"
      sudo rm -f "$ENABLED_LINK"
    fi
    
    # 创建新的软链接
    echo "  创建软链接: $ENABLED_LINK -> $SITE_FILE"
    sudo ln -sf "$SITE_FILE" "$ENABLED_LINK"
    
    if [ -L "$ENABLED_LINK" ]; then
      echo "  ✅ $SITE 已启用"
      ENABLED_COUNT=$((ENABLED_COUNT + 1))
    else
      echo "  ❌ $SITE 启用失败"
    fi
  else
    echo "⚠️  站点配置不存在: $SITE_FILE"
  fi
done

echo ""
echo "已启用 $ENABLED_COUNT 个站点配置"
echo ""

# 3. 检查是否有其他站点配置需要启用
echo "3. 检查其他站点配置..."
echo "----------------------------------------"
OTHER_SITES=$(ls "$SITES_AVAILABLE_DIR" 2>/dev/null | grep -v "^default$" | grep -v "^\.$" | grep -v "^\.\.$" || true)

if [ -n "$OTHER_SITES" ]; then
  echo "发现其他站点配置："
  for OTHER_SITE in $OTHER_SITES; do
    # 检查是否已经在启用列表中
    FOUND=false
    for SITE in "${SITES[@]}"; do
      if [ "$OTHER_SITE" = "$SITE" ]; then
        FOUND=true
        break
      fi
    done
    
    if [ "$FOUND" = false ]; then
      echo "  - $OTHER_SITE"
      SITE_FILE="$SITES_AVAILABLE_DIR/$OTHER_SITE"
      ENABLED_LINK="$SITES_ENABLED_DIR/$OTHER_SITE"
      
      # 检查是否已经启用
      if [ ! -L "$ENABLED_LINK" ] && [ ! -f "$ENABLED_LINK" ]; then
        echo "    是否启用此站点？(y/n，默认 n)"
        # 在非交互模式下，默认不启用
        # 如果需要自动启用，可以取消下面的注释
        # sudo ln -sf "$SITE_FILE" "$ENABLED_LINK"
        # echo "    ✅ $OTHER_SITE 已启用"
      fi
    fi
  done
fi
echo ""

# 4. 测试 Nginx 配置
echo "4. 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置有错误"
  echo "请检查配置文件的语法错误"
  exit 1
fi
echo ""

# 5. 重启 Nginx
echo "5. 重启 Nginx..."
echo "----------------------------------------"
if sudo systemctl restart nginx; then
  echo "✅ Nginx 已重启"
  
  # 等待 Nginx 启动
  sleep 2
  
  # 检查 Nginx 状态
  if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
  else
    echo "❌ Nginx 启动失败"
    sudo systemctl status nginx --no-pager | head -15
    exit 1
  fi
else
  echo "❌ Nginx 重启失败"
  sudo systemctl status nginx --no-pager | head -15
  exit 1
fi
echo ""

# 6. 验证
echo "6. 验证配置..."
echo "----------------------------------------"

# 列出启用的站点
echo "已启用的站点配置："
ls -la "$SITES_ENABLED_DIR" 2>/dev/null | grep -v "^total" | grep -v "^\.$" | grep -v "^\.\.$" || echo "⚠️  没有启用的站点配置"
echo ""

# 检查 Nginx 监听状态
echo "Nginx 监听状态："
if command -v netstat >/dev/null 2>&1; then
  sudo netstat -ntlp | grep nginx || echo "⚠️  未找到 Nginx 监听端口"
elif command -v ss >/dev/null 2>&1; then
  sudo ss -tlnp | grep nginx || echo "⚠️  未找到 Nginx 监听端口"
else
  echo "⚠️  netstat 和 ss 都不可用"
fi
echo ""

# 检查端口 80 和 443
echo "检查端口 80 和 443："
for PORT in 80 443; do
  if ss -tlnp 2>/dev/null | grep -q ":$PORT " || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    PROCESS=$(ss -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $NF}' || netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' || echo "未知")
    echo "✅ 端口 $PORT 正在监听 - 进程: $PROCESS"
  else
    echo "❌ 端口 $PORT 未监听"
  fi
done
echo ""

# 测试 HTTP 响应
echo "测试 HTTP 响应..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:80 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
  echo "✅ 端口 80 HTTP 响应正常 (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "403" ]; then
  echo "⚠️  端口 80 返回 403 Forbidden（可能是配置问题）"
elif [ "$HTTP_CODE" = "000" ]; then
  echo "❌ 端口 80 无法连接"
else
  echo "⚠️  端口 80 HTTP 响应异常 (HTTP $HTTP_CODE)"
fi
echo ""

# 显示 Nginx 错误日志（如果有）
if [ -f "/var/log/nginx/error.log" ]; then
  ERROR_COUNT=$(sudo tail -20 /var/log/nginx/error.log | grep -i error | wc -l)
  if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Nginx 错误日志中有 $ERROR_COUNT 个错误："
    sudo tail -10 /var/log/nginx/error.log | grep -i error || true
  else
    echo "✅ Nginx 错误日志正常"
  fi
fi
echo ""

echo "=========================================="
echo "✅ Nginx 站点配置恢复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "已启用的站点："
for SITE in "${SITES[@]}"; do
  if [ -L "$SITES_ENABLED_DIR/$SITE" ]; then
    echo "  ✅ $SITE"
  else
    echo "  ❌ $SITE (未启用)"
  fi
done
echo ""
echo "如果仍有问题，请检查："
echo "  sudo nginx -T"
echo "  sudo tail -50 /var/log/nginx/error.log"
echo "  sudo systemctl status nginx"
