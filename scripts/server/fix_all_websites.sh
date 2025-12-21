#!/bin/bash

# 修复所有网站黑屏问题脚本
# 使用方法: bash scripts/server/fix_all_websites.sh

set -e

echo "=========================================="
echo "🔧 修复所有网站黑屏问题"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 先运行诊断
echo "1. 运行诊断..."
echo "----------------------------------------"
bash scripts/server/diagnose_all_services.sh
echo ""

# 2. 停止所有服务
echo "2. 停止所有服务..."
echo "----------------------------------------"
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true
sleep 2

# 停止占用端口的进程
PORTS=(3000 3001 3002 3003 8000)
for PORT in "${PORTS[@]}"; do
  if ss -tlnp 2>/dev/null | grep -q ":$PORT " || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "停止占用端口 $PORT 的进程..."
    PIDS=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP "pid=\K\d+" || netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1 || echo "")
    for PID in $PIDS; do
      if [ -n "$PID" ] && [ "$PID" != "N/A" ] && [ "$PID" != "Address" ]; then
        sudo kill -9 $PID 2>/dev/null || true
      fi
    done
    sleep 1
  fi
done
echo "✅ 所有服务已停止"
echo ""

# 3. 启动后端
echo "3. 启动后端服务..."
echo "----------------------------------------"
bash scripts/server/fix_backend_deps.sh
echo ""

# 4. 启动所有前端服务（使用之前的终极修复脚本）
echo "4. 启动所有前端服务..."
echo "----------------------------------------"
if [ -f "scripts/server/force_start_4_sites.sh" ]; then
  bash scripts/server/force_start_4_sites.sh
else
  echo "⚠️  force_start_4_sites.sh 不存在，手动启动服务..."
  
  # 手动启动 saas-demo (3000)
  if [ -d "saas-demo" ]; then
    cd saas-demo
    if [ ! -d "node_modules" ]; then
      npm install
    fi
    if [ ! -d ".next" ]; then
      npm run build
    fi
    pm2 start npm --name saas-demo -- start
    cd "$PROJECT_ROOT"
  fi
  
  # 手动启动其他前端服务...
  # (这里可以添加其他服务的启动逻辑)
fi
echo ""

# 5. 等待服务启动
echo "5. 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 6. 重启 Nginx
echo "6. 重启 Nginx..."
echo "----------------------------------------"
sudo systemctl restart nginx
sleep 2

if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 已重启"
else
  echo "⚠️  Nginx 重启失败，尝试启动..."
  sudo systemctl start nginx
fi
echo ""

# 7. 验证所有服务
echo "7. 验证所有服务..."
echo "----------------------------------------"
pm2 list
echo ""

# 测试端口
echo "测试端口响应..."
for PORT in 3000 3001 3002 3003; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$PORT 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 端口 $PORT HTTP 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "❌ 端口 $PORT HTTP 响应异常 (HTTP $HTTP_CODE)"
    echo "   检查服务日志: pm2 logs $(pm2 list | grep -E "3000|3001|3002|3003" | awk '{print $2}' | head -1) --lines 20"
  fi
done
echo ""

# 8. 保存 PM2 配置
echo "8. 保存 PM2 配置..."
echo "----------------------------------------"
pm2 save
echo "✅ PM2 配置已保存"
echo ""

echo "=========================================="
echo "✅ 所有网站修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果网站仍然无法访问，请检查："
echo "  1. Nginx 配置: sudo nginx -t"
echo "  2. Nginx 日志: sudo tail -50 /var/log/nginx/error.log"
echo "  3. PM2 日志: pm2 logs"
echo "  4. 端口监听: ss -tlnp | grep -E '3000|3001|3002|3003'"
