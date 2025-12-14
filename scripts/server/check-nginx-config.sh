#!/bin/bash
# ============================================================
# 检查 Nginx 配置（用于 502 错误诊断）
# ============================================================

set +e

echo "=========================================="
echo "🔍 检查 Nginx 配置"
echo "=========================================="
echo ""

# 检查 Nginx 配置语法
echo "[1/4] 检查 Nginx 配置语法..."
sudo nginx -t

# 显示相关配置
echo ""
echo "[2/4] 显示后端代理配置..."
NGINX_CONFIG="/etc/nginx/sites-available/default"
if [ -f "$NGINX_CONFIG" ]; then
  echo "配置文件: $NGINX_CONFIG"
  echo ""
  echo "--- upstream 配置 ---"
  grep -A 10 "upstream" "$NGINX_CONFIG" || echo "未找到 upstream 配置"
  echo ""
  echo "--- proxy_pass 配置 ---"
  grep -B 5 -A 10 "proxy_pass" "$NGINX_CONFIG" || echo "未找到 proxy_pass 配置"
else
  echo "配置文件不存在: $NGINX_CONFIG"
fi

# 检查 Nginx 状态
echo ""
echo "[3/4] 检查 Nginx 服务状态..."
systemctl status nginx --no-pager -l | head -20

# 检查错误日志
echo ""
echo "[4/4] 最近的 Nginx 错误日志..."
if [ -f "/var/log/nginx/error.log" ]; then
  sudo tail -30 /var/log/nginx/error.log
else
  echo "错误日志文件不存在"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="
echo ""

