#!/bin/bash

echo "=========================================="
echo "🔍 检查前端服务状态"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 网站配置：域名 -> 端口 -> 目录
declare -A SITES=(
  ["tgmini"]="3001:tgmini20251220"
  ["hongbao"]="3002:hbwy20251220"
  ["aizkw"]="3003:aizkw20251219"
)

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

echo "1️⃣ 检查端口监听状态..."
echo "----------------------------------------"
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir <<< "${SITES[$site]}"
  PORT_STATUS=$(sudo netstat -tlnp 2>/dev/null | grep ":$port " || sudo ss -tlnp 2>/dev/null | grep ":$port " || echo "")
  if [ -n "$PORT_STATUS" ]; then
    echo "✅ 端口 $port ($site) 正在监听"
    echo "   $PORT_STATUS"
  else
    echo "❌ 端口 $port ($site) 未监听"
  fi
  echo ""
done

echo "2️⃣ 检查 PM2 进程..."
echo "----------------------------------------"
if command -v pm2 >/dev/null 2>&1; then
  pm2 list
  echo ""
  
  # 检查每个前端服务
  for site in "${!SITES[@]}"; do
    IFS=':' read -r port dir <<< "${SITES[$site]}"
    PM2_NAME="${site}-frontend"
    
    if pm2 list | grep -q "$PM2_NAME"; then
      echo "✅ PM2 进程存在: $PM2_NAME"
      pm2 describe "$PM2_NAME" | grep -E "status|pid|uptime|restarts" || true
    else
      echo "❌ PM2 进程不存在: $PM2_NAME"
    fi
    echo ""
  done
else
  echo "⚠️  PM2 未安装"
  echo ""
fi

echo "3️⃣ 检查项目目录和 dist 文件夹..."
echo "----------------------------------------"
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir <<< "${SITES[$site]}"
  SITE_DIR="$PROJECT_DIR/$dir"
  
  echo "网站: $site"
  echo "目录: $SITE_DIR"
  
  if [ -d "$SITE_DIR" ]; then
    echo "  ✅ 目录存在"
    
    if [ -d "$SITE_DIR/dist" ]; then
      echo "  ✅ dist 目录存在"
      DIST_SIZE=$(du -sh "$SITE_DIR/dist" 2>/dev/null | cut -f1 || echo "未知")
      echo "  📦 dist 大小: $DIST_SIZE"
      
      # 检查是否有文件
      FILE_COUNT=$(find "$SITE_DIR/dist" -type f 2>/dev/null | wc -l)
      echo "  📄 文件数量: $FILE_COUNT"
      
      if [ "$FILE_COUNT" -eq 0 ]; then
        echo "  ⚠️  警告: dist 目录为空，需要构建"
      fi
    else
      echo "  ❌ dist 目录不存在，需要构建"
    fi
    
    # 检查启动脚本
    if [ -f "$SITE_DIR/start-frontend.sh" ]; then
      echo "  ✅ 启动脚本存在: start-frontend.sh"
    else
      echo "  ❌ 启动脚本不存在: start-frontend.sh"
    fi
  else
    echo "  ❌ 目录不存在"
  fi
  echo ""
done

echo "4️⃣ 测试本地端口连接..."
echo "----------------------------------------"
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir <<< "${SITES[$site]}"
  
  echo "测试端口 $port ($site)..."
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 http://127.0.0.1:$port 2>/dev/null || echo "000")
  
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "  ✅ 端口 $port 响应正常 (HTTP $HTTP_CODE)"
  elif [ "$HTTP_CODE" = "000" ]; then
    echo "  ❌ 端口 $port 无法连接（服务未运行）"
  else
    echo "  ⚠️  端口 $port 响应异常 (HTTP $HTTP_CODE)"
  fi
  echo ""
done

echo "=========================================="
echo "✅ 检查完成"
echo "时间: $(date)"
echo "=========================================="
