#!/bin/bash

# 修正 aikz.usdt2026.cc 端口映射（3003 -> 3000）
# 使用方法: bash scripts/server/fix_aikz_port.sh

set -e

echo "=========================================="
echo "🔧 修正 aikz.usdt2026.cc 端口映射"
echo "时间: $(date)"
echo "=========================================="
echo ""

AIKZ_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"
AIKZ_ENABLED="/etc/nginx/sites-enabled/aikz.usdt2026.cc"

# 1. 检查配置文件是否存在
echo "1. 检查配置文件..."
echo "----------------------------------------"
if [ ! -f "$AIKZ_CONFIG" ]; then
  echo "❌ 配置文件不存在: $AIKZ_CONFIG"
  exit 1
fi

echo "✅ 找到配置文件: $AIKZ_CONFIG"
echo ""

# 2. 显示当前配置
echo "2. 当前配置（proxy_pass 部分）..."
echo "----------------------------------------"
grep "proxy_pass" "$AIKZ_CONFIG" || echo "⚠️  未找到 proxy_pass 配置"
echo ""

# 3. 备份原配置
echo "3. 备份原配置..."
echo "----------------------------------------"
BACKUP_FILE="${AIKZ_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp "$AIKZ_CONFIG" "$BACKUP_FILE"
echo "✅ 配置已备份到: $BACKUP_FILE"
echo ""

# 4. 修改配置：将 3003 替换为 3000
echo "4. 修改配置（将 3003 替换为 3000）..."
echo "----------------------------------------"

# 统计替换前的数量
BEFORE_COUNT=$(grep -c "127.0.0.1:3003" "$AIKZ_CONFIG" 2>/dev/null || echo "0")
echo "找到 $BEFORE_COUNT 个需要替换的配置"

if [ "$BEFORE_COUNT" -eq 0 ]; then
  echo "⚠️  未找到需要替换的配置（可能已经是 3000）"
  # 检查是否已经是 3000
  if grep -q "127.0.0.1:3000" "$AIKZ_CONFIG"; then
    echo "✅ 配置已经是 3000，无需修改"
    exit 0
  else
    echo "❌ 配置中既没有 3003 也没有 3000，请检查配置"
    exit 1
  fi
fi

# 执行替换：将所有 127.0.0.1:3003 替换为 127.0.0.1:3000
sudo sed -i 's|127.0.0.1:3003|127.0.0.1:3000|g' "$AIKZ_CONFIG"

# 验证替换结果
AFTER_COUNT=$(grep -c "127.0.0.1:3000" "$AIKZ_CONFIG" 2>/dev/null || echo "0")
REMAINING_COUNT=$(grep -c "127.0.0.1:3003" "$AIKZ_CONFIG" 2>/dev/null || echo "0")

if [ "$REMAINING_COUNT" -eq 0 ] && [ "$AFTER_COUNT" -gt 0 ]; then
  echo "✅ 配置已修改：$BEFORE_COUNT 个配置已从 3003 改为 3000"
elif [ "$REMAINING_COUNT" -gt 0 ]; then
  echo "⚠️  仍有 $REMAINING_COUNT 个配置未替换，尝试再次替换..."
  sudo sed -i 's|3003|3000|g' "$AIKZ_CONFIG"
  echo "✅ 再次替换完成"
else
  echo "❌ 替换失败，请检查配置"
  exit 1
fi
echo ""

# 5. 显示修改后的配置
echo "5. 修改后的配置（proxy_pass 部分）..."
echo "----------------------------------------"
grep "proxy_pass" "$AIKZ_CONFIG" || echo "⚠️  未找到 proxy_pass 配置"
echo ""

# 6. 验证配置（确认已改为 3000）
echo "6. 验证配置..."
echo "----------------------------------------"
if grep -q "proxy_pass.*127.0.0.1:3000" "$AIKZ_CONFIG"; then
  echo "✅ 确认：配置已指向端口 3000"
  echo ""
  echo "所有 proxy_pass 配置："
  grep "proxy_pass" "$AIKZ_CONFIG" | while read line; do
    if echo "$line" | grep -q "3000"; then
      echo "  ✅ $line"
    elif echo "$line" | grep -q "3003"; then
      echo "  ❌ $line (仍然是 3003)"
    else
      echo "  ⚠️  $line"
    fi
  done
else
  echo "❌ 配置中未找到指向端口 3000 的 proxy_pass"
  echo "显示完整配置："
  cat "$AIKZ_CONFIG"
  exit 1
fi
echo ""

# 7. 测试 Nginx 配置
echo "7. 测试 Nginx 配置..."
echo "----------------------------------------"
if sudo nginx -t 2>&1; then
  echo "✅ Nginx 配置语法正确"
else
  echo "❌ Nginx 配置有错误"
  echo "恢复备份配置..."
  sudo cp "$BACKUP_FILE" "$AIKZ_CONFIG"
  echo "✅ 已恢复备份配置"
  exit 1
fi
echo ""

# 8. 重启 Nginx
echo "8. 重启 Nginx..."
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

# 9. 最终验证
echo "9. 最终验证..."
echo "----------------------------------------"

# 检查启用的配置
if [ -L "$AIKZ_ENABLED" ] || [ -f "$AIKZ_ENABLED" ]; then
  echo "检查启用的配置中的 proxy_pass："
  grep "proxy_pass" "$AIKZ_ENABLED" || echo "⚠️  未找到 proxy_pass"
  
  # 验证所有 proxy_pass 都指向 3000
  WRONG_COUNT=$(grep "proxy_pass" "$AIKZ_ENABLED" | grep -c "3003" || echo "0")
  CORRECT_COUNT=$(grep "proxy_pass" "$AIKZ_ENABLED" | grep -c "3000" || echo "0")
  
  if [ "$WRONG_COUNT" -eq 0 ] && [ "$CORRECT_COUNT" -gt 0 ]; then
    echo "✅ 所有 proxy_pass 都正确指向端口 3000"
  elif [ "$WRONG_COUNT" -gt 0 ]; then
    echo "❌ 仍有 $WRONG_COUNT 个 proxy_pass 指向 3003"
    exit 1
  fi
else
  echo "⚠️  启用的配置不存在，检查软链接..."
  ls -la /etc/nginx/sites-enabled/ | grep aikz || echo "⚠️  未找到 aikz 软链接"
fi
echo ""

# 检查端口 3000 是否监听
if ss -tlnp 2>/dev/null | grep -q ":3000 " || netstat -tlnp 2>/dev/null | grep -q ":3000 "; then
  echo "✅ 端口 3000 正在监听"
  
  # 测试端口 3000 HTTP 响应
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:3000 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ 端口 3000 HTTP 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  端口 3000 HTTP 响应异常 (HTTP $HTTP_CODE)"
  fi
else
  echo "❌ 端口 3000 未监听"
  echo "   请检查 saas-demo 服务是否运行: pm2 list | grep saas-demo"
fi
echo ""

echo "=========================================="
echo "✅ 端口映射修正完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "配置摘要："
echo "  - aikz.usdt2026.cc -> http://127.0.0.1:3000 (saas-demo, Next.js)"
echo "  - 配置文件: $AIKZ_CONFIG"
echo "  - 备份文件: $BACKUP_FILE"
echo ""
echo "验证命令："
echo "  grep 'proxy_pass' /etc/nginx/sites-enabled/aikz.usdt2026.cc"
echo "  curl -I http://aikz.usdt2026.cc"
echo ""
echo "如果仍有问题，请检查："
echo "  sudo nginx -T | grep -A 10 'aikz.usdt2026.cc'"
echo "  sudo tail -20 /var/log/nginx/error.log"
echo "  pm2 logs saas-demo --lines 20"
