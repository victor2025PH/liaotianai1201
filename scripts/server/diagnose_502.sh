#!/bin/bash
# ============================================================
# 诊断 502 错误
# ============================================================

set -e

# 自动检测项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ ! -d "$PROJECT_ROOT/saas-demo" ] && [ ! -d "$PROJECT_ROOT/admin-backend" ]; then
  if [ -d "/home/ubuntu/telegram-ai-system" ]; then
    PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
  else
    echo "❌ 无法找到项目根目录"
    exit 1
  fi
fi

echo "=========================================="
echo "🔍 诊断 502 错误"
echo "时间: $(date)"
echo "项目根目录: $PROJECT_ROOT"
echo "=========================================="
echo ""

echo "=== 1. PM2 进程状态 ==="
pm2 list
echo ""

echo "=== 2. 端口监听状态 ==="
echo "检查关键端口 (8000, 3005, 3001, 3002, 3003):"
netstat -tlnp 2>/dev/null | grep -E "8000|3005|3001|3002|3003" || echo "没有服务在监听这些端口"
echo ""

echo "=== 3. 服务健康检查 ==="
echo "测试后端 (8000):"
curl -I http://127.0.0.1:8000/api/health 2>&1 | head -3 || echo "❌ 后端服务无响应"
echo ""

echo "测试前端 (3005):"
curl -I http://127.0.0.1:3005 2>&1 | head -3 || echo "❌ 前端服务无响应"
echo ""

echo "测试 tgmini (3001):"
curl -I http://127.0.0.1:3001 2>&1 | head -3 || echo "❌ tgmini 服务无响应"
echo ""

echo "测试 hongbao (3002):"
curl -I http://127.0.0.1:3002 2>&1 | head -3 || echo "❌ hongbao 服务无响应"
echo ""

echo "测试 aizkw (3003):"
curl -I http://127.0.0.1:3003 2>&1 | head -3 || echo "❌ aizkw 服务无响应"
echo ""

echo "=== 4. 服务错误日志（最后 10 行）==="
echo "--- backend ---"
pm2 logs backend --err --lines 10 --nostream 2>/dev/null || echo "无法获取日志"
echo ""

echo "--- saas-demo-frontend ---"
pm2 logs saas-demo-frontend --err --lines 10 --nostream 2>/dev/null || echo "无法获取日志"
echo ""

echo "=== 5. Nginx 状态 ==="
sudo systemctl status nginx --no-pager | head -10 || echo "无法获取 Nginx 状态"
echo ""

echo "=== 6. Nginx 错误日志（最后 10 行）==="
sudo tail -10 /var/log/nginx/error.log 2>/dev/null || echo "无法读取 Nginx 错误日志"
echo ""

echo "=========================================="
echo "✅ 诊断完成"
echo "=========================================="
