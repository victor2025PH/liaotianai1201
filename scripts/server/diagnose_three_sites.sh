#!/bin/bash
# ============================================================
# 诊断三个网站的状态
# ============================================================

set -e

PROJECT_ROOT="/home/***/telegram-ai-system"

echo "=========================================="
echo "🔍 诊断三个网站状态"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 定义网站配置
declare -A SITES=(
  ["tgmini"]="3001:tgmini20251220:tgmini-frontend:tgmini.usdt2026.cc"
  ["hongbao"]="3002:hbwy20251220:hongbao-frontend:hongbao.usdt2026.cc"
  ["aizkw"]="3003:aizkw20251219:aizkw-frontend:aizkw.usdt2026.cc"
)

echo "=== 1. PM2 进程状态 ==="
pm2 list
echo ""

echo "=== 2. 端口监听状态 ==="
netstat -tlnp | grep -E "3001|3002|3003" || echo "没有服务在监听 3001/3002/3003"
echo ""

echo "=== 3. 检查项目目录和构建产物 ==="
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir pm2_name domain <<< "${SITES[$site]}"
  echo "--- $site (端口 $port, 目录 $dir) ---"
  
  PROJECT_DIR="$PROJECT_ROOT/$dir"
  if [ -d "$PROJECT_DIR" ]; then
    echo "  ✅ 目录存在: $PROJECT_DIR"
    
    if [ -d "$PROJECT_DIR/dist" ]; then
      echo "  ✅ dist 目录存在"
      echo "  dist 目录大小: $(du -sh "$PROJECT_DIR/dist" 2>/dev/null | cut -f1)"
    else
      echo "  ❌ dist 目录不存在（需要构建）"
    fi
    
    if [ -f "$PROJECT_DIR/package.json" ]; then
      echo "  ✅ package.json 存在"
    else
      echo "  ❌ package.json 不存在"
    fi
  else
    echo "  ❌ 目录不存在: $PROJECT_DIR"
  fi
  echo ""
done

echo "=== 4. 本地服务测试 ==="
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir pm2_name domain <<< "${SITES[$site]}"
  echo "测试 $site (端口 $port):"
  curl -I http://127.0.0.1:$port 2>&1 | head -3 || echo "  ❌ 连接失败"
  echo ""
done

echo "=== 5. Nginx 配置检查 ==="
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir pm2_name domain <<< "${SITES[$site]}"
  echo "--- $domain (应该代理到端口 $port) ---"
  CONFIG_FILE="/etc/nginx/sites-enabled/$domain"
  if [ -f "$CONFIG_FILE" ]; then
    echo "  ✅ 配置文件存在"
    if grep -q "proxy_pass.*127.0.0.1:$port" "$CONFIG_FILE"; then
      echo "  ✅ proxy_pass 配置正确 (指向端口 $port)"
    else
      echo "  ❌ proxy_pass 配置错误或未找到"
      echo "  当前配置:"
      grep "proxy_pass" "$CONFIG_FILE" || echo "    未找到 proxy_pass"
    fi
  else
    echo "  ❌ 配置文件不存在: $CONFIG_FILE"
  fi
  echo ""
done

echo "=== 6. PM2 服务日志（最后 5 行）==="
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir pm2_name domain <<< "${SITES[$site]}"
  echo "--- $pm2_name ---"
  pm2 logs "$pm2_name" --lines 5 --nostream 2>/dev/null || echo "  ⚠️  无法获取日志（服务可能未运行）"
  echo ""
done

echo "=========================================="
echo "✅ 诊断完成"
echo "=========================================="
