#!/bin/bash

set -e

echo "=========================================="
echo "🚀 启动所有前端服务"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 确保以 root 权限运行（或使用 sudo）
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  此脚本需要 sudo 权限，请使用: sudo bash $0"
  exit 1
fi

# 网站配置：域名 -> 端口 -> 目录 -> PM2名称
declare -A SITES=(
  ["tgmini"]="3001:tgmini20251220:tgmini-frontend"
  ["hongbao"]="3002:hbwy20251220:hongbao-frontend"
  ["aizkw"]="3003:aizkw20251219:aizkw-frontend"
)

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

# 检查 PM2 是否安装
if ! command -v pm2 >/dev/null 2>&1; then
  echo "⚠️  PM2 未安装，安装 PM2..."
  npm install -g pm2 || {
    echo "❌ PM2 安装失败"
    exit 1
  }
  pm2 startup systemd -u ubuntu --hp /home/ubuntu || true
fi

# 检查 serve 是否安装
if ! command -v serve >/dev/null 2>&1; then
  echo "⚠️  serve 未安装，安装 serve..."
  npm install -g serve || {
    echo "❌ serve 安装失败"
    exit 1
  }
fi

echo "✅ PM2 和 serve 已安装"
echo ""

# 处理每个网站
SUCCESS_COUNT=0
FAILED_SITES=()

for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir pm2_name <<< "${SITES[$site]}"
  SITE_DIR="$PROJECT_DIR/$dir"
  
  echo "=========================================="
  echo "📝 处理网站: $site"
  echo "目录: $SITE_DIR"
  echo "端口: $port"
  echo "PM2 名称: $pm2_name"
  echo "=========================================="
  echo ""
  
  # 检查目录是否存在
  if [ ! -d "$SITE_DIR" ]; then
    echo "❌ 目录不存在: $SITE_DIR"
    FAILED_SITES+=("$site (目录不存在)")
    continue
  fi
  
  # 检查 dist 目录
  if [ ! -d "$SITE_DIR/dist" ]; then
    echo "❌ dist 目录不存在: $SITE_DIR/dist"
    echo "   需要先构建项目"
    FAILED_SITES+=("$site (dist 不存在)")
    continue
  fi
  
  # 检查 dist 目录是否为空
  FILE_COUNT=$(find "$SITE_DIR/dist" -type f 2>/dev/null | wc -l)
  if [ "$FILE_COUNT" -eq 0 ]; then
    echo "❌ dist 目录为空，需要构建项目"
    FAILED_SITES+=("$site (dist 为空)")
    continue
  fi
  
  echo "✅ dist 目录存在且不为空 ($FILE_COUNT 个文件)"
  
  # 停止可能运行在端口的进程
  if sudo lsof -i :$port >/dev/null 2>&1; then
    echo "停止占用端口 $port 的进程..."
    sudo lsof -ti :$port | xargs sudo kill -9 2>/dev/null || true
    sleep 1
  fi
  
  # 停止并删除 PM2 旧进程
  pm2 delete "$pm2_name" 2>/dev/null || true
  
  # 确保日志目录存在
  mkdir -p "$SITE_DIR/logs"
  
  # 生成启动脚本
  START_SCRIPT="$SITE_DIR/start-frontend.sh"
  cat > "$START_SCRIPT" <<EOF
#!/bin/bash
# 前端服务启动脚本
# 使用全局 serve 命令启动静态文件服务
set -e
DIST_DIR="$SITE_DIR/dist"
PORT=$port

# 检查 serve 命令是否存在
if ! command -v serve >/dev/null 2>&1; then
  echo "错误: serve 命令未找到，请先安装: npm install -g serve"
  exit 1
fi

# 检查 dist 目录是否存在
if [ ! -d "\$DIST_DIR" ]; then
  echo "错误: dist 目录不存在: \$DIST_DIR"
  exit 1
fi

# 启动 serve
exec serve -s "\$DIST_DIR" -l "\$PORT" --no-clipboard
EOF
  
  chmod +x "$START_SCRIPT"
  echo "✅ 启动脚本已生成: $START_SCRIPT"
  
  # 使用 PM2 启动脚本
  echo "使用 PM2 启动前端服务..."
  pm2 start "$START_SCRIPT" \
    --name "$pm2_name" \
    --error "$SITE_DIR/logs/frontend-error.log" \
    --output "$SITE_DIR/logs/frontend-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" || {
    echo "⚠️  PM2 启动失败，查看错误..."
    pm2 logs "$pm2_name" --lines 10 --nostream 2>/dev/null || true
    FAILED_SITES+=("$site (PM2 启动失败)")
    continue
  }
  
  pm2 save || true
  echo "✅ PM2 应用已启动"
  
  # 等待启动
  echo "等待服务启动..."
  sleep 5
  
  # 检查端口是否在监听
  if sudo lsof -i :$port >/dev/null 2>&1; then
    echo "✅ 端口 $port 正在监听"
    
    # 测试连接
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 http://127.0.0.1:$port 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
      echo "✅ 服务响应正常 (HTTP $HTTP_CODE)"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
      echo "⚠️  服务响应异常 (HTTP $HTTP_CODE)"
      FAILED_SITES+=("$site (响应异常: $HTTP_CODE)")
    fi
  else
    echo "❌ 端口 $port 未在监听"
    echo "查看 PM2 日志..."
    pm2 logs "$pm2_name" --lines 20 --nostream 2>/dev/null || true
    FAILED_SITES+=("$site (端口未监听)")
  fi
  
  echo ""
done

# 保存 PM2 配置
pm2 save || true

echo "=========================================="
echo "📊 启动结果汇总"
echo "=========================================="
echo "成功: $SUCCESS_COUNT / ${#SITES[@]}"
if [ ${#FAILED_SITES[@]} -gt 0 ]; then
  echo "失败: ${#FAILED_SITES[@]}"
  echo "失败的网站:"
  for failed in "${FAILED_SITES[@]}"; do
    echo "  - $failed"
  done
fi
echo ""

echo "当前 PM2 进程列表:"
pm2 list
echo ""

echo "=========================================="
echo "✅ 启动完成！"
echo "时间: $(date)"
echo "=========================================="

if [ ${#FAILED_SITES[@]} -gt 0 ]; then
  echo ""
  echo "⚠️  部分网站启动失败，请检查："
  echo "1. 项目是否已构建（dist 目录是否存在且不为空）"
  echo "2. PM2 日志: pm2 logs"
  echo "3. 手动启动: pm2 start [启动脚本路径]"
  exit 1
fi
