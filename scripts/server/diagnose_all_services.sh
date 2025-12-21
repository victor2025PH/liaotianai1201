#!/bin/bash

# 全面诊断所有服务状态脚本
# 使用方法: bash scripts/server/diagnose_all_services.sh

set -e

echo "=========================================="
echo "🔍 全面诊断所有服务状态"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 检查 PM2 服务状态
echo "1. 检查 PM2 服务状态..."
echo "----------------------------------------"
pm2 list
echo ""

# 2. 检查端口监听状态
echo "2. 检查端口监听状态..."
echo "----------------------------------------"
PORTS=(3000 3001 3002 3003 8000)
for PORT in "${PORTS[@]}"; do
  if ss -tlnp 2>/dev/null | grep -q ":$PORT " || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    PROCESS=$(ss -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $NF}' || netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' || echo "未知")
    echo "✅ 端口 $PORT 正在监听 - 进程: $PROCESS"
  else
    echo "❌ 端口 $PORT 未监听"
  fi
done
echo ""

# 3. 测试 HTTP 响应
echo "3. 测试 HTTP 响应..."
echo "----------------------------------------"
for PORT in 3000 3001 3002 3003; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 端口 $PORT HTTP 响应正常 (HTTP $HTTP_CODE)"
  elif [ "$HTTP_CODE" = "000" ]; then
    echo "❌ 端口 $PORT 无法连接"
  else
    echo "⚠️  端口 $PORT HTTP 响应异常 (HTTP $HTTP_CODE)"
  fi
done

# 后端端口
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:8000/docs 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
  echo "✅ 端口 8000 (后端) HTTP 响应正常 (HTTP $HTTP_CODE)"
else
  echo "⚠️  端口 8000 (后端) HTTP 响应异常 (HTTP $HTTP_CODE)"
fi
echo ""

# 4. 检查 Nginx 状态
echo "4. 检查 Nginx 状态..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 正在运行"
  systemctl status nginx --no-pager | head -5
else
  echo "❌ Nginx 未运行"
fi
echo ""

# 5. 检查各个前端服务日志
echo "5. 检查各个前端服务日志（最近 10 行）..."
echo "----------------------------------------"
SERVICES=("saas-demo" "tgmini-frontend" "hongbao-frontend" "aizkw-frontend" "backend")
for SERVICE in "${SERVICES[@]}"; do
  if pm2 list | grep -q "$SERVICE"; then
    echo "--- $SERVICE 日志 ---"
    pm2 logs "$SERVICE" --lines 10 --nostream 2>/dev/null | tail -10 || echo "无法获取日志"
    echo ""
  else
    echo "⚠️  $SERVICE 未在 PM2 中运行"
    echo ""
  fi
done

# 6. 检查前端构建目录
echo "6. 检查前端构建目录..."
echo "----------------------------------------"
FRONTEND_PROJECTS=(
  "saas-demo:.next"
  "react-vite-template/hbwy20251220:dist"
)

for PROJECT in "${FRONTEND_PROJECTS[@]}"; do
  DIR=$(echo "$PROJECT" | cut -d: -f1)
  BUILD_DIR=$(echo "$PROJECT" | cut -d: -f2)
  FULL_PATH="$PROJECT_ROOT/$DIR/$BUILD_DIR"
  
  if [ -d "$FULL_PATH" ]; then
    SIZE=$(du -sh "$FULL_PATH" 2>/dev/null | awk '{print $1}')
    echo "✅ $DIR/$BUILD_DIR 存在 (大小: $SIZE)"
  else
    echo "❌ $DIR/$BUILD_DIR 不存在"
  fi
done
echo ""

# 7. 检查 Nginx 配置
echo "7. 检查 Nginx 配置..."
echo "----------------------------------------"
if [ -d "/etc/nginx/sites-enabled" ]; then
  ENABLED_SITES=$(ls /etc/nginx/sites-enabled/ 2>/dev/null | wc -l)
  echo "已启用的 Nginx 站点: $ENABLED_SITES"
  ls -la /etc/nginx/sites-enabled/ 2>/dev/null | tail -5 || echo "无法列出站点"
else
  echo "⚠️  Nginx sites-enabled 目录不存在"
fi
echo ""

# 8. 测试 Nginx 配置
echo "8. 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置有错误"
fi
echo ""

echo "=========================================="
echo "诊断完成！"
echo "时间: $(date)"
echo "=========================================="
