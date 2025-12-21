#!/bin/bash

set -e

echo "=========================================="
echo "🔨 构建并启动所有前端服务"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 确保以 root 权限运行
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

# 检查项目根目录
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ 项目目录不存在: $PROJECT_DIR"
  exit 1
fi

cd "$PROJECT_DIR"

# 拉取最新代码
echo "📥 拉取最新代码..."
echo "----------------------------------------"
git fetch origin main || git fetch origin || true
git pull origin main || {
  echo "⚠️  Git pull 失败，继续执行..."
}
echo ""

# 检查并安装 Node.js 和 npm
if ! command -v node >/dev/null 2>&1; then
  echo "⚠️  Node.js 未安装，安装 Node.js..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "⚠️  npm 未安装，安装 npm..."
  apt-get install -y npm
fi

echo "✅ Node.js: $(node --version)"
echo "✅ npm: $(npm --version)"
echo ""

# 检查并安装 PM2 和 serve
if ! command -v pm2 >/dev/null 2>&1; then
  echo "⚠️  PM2 未安装，安装 PM2..."
  npm install -g pm2
  pm2 startup systemd -u ubuntu --hp /home/ubuntu || true
fi

if ! command -v serve >/dev/null 2>&1; then
  echo "⚠️  serve 未安装，安装 serve..."
  npm install -g serve
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
  echo "=========================================="
  echo ""
  
  # 检查目录是否存在
  if [ ! -d "$SITE_DIR" ]; then
    echo "❌ 目录不存在: $SITE_DIR"
    FAILED_SITES+=("$site (目录不存在)")
    continue
  fi
  
  cd "$SITE_DIR"
  
  # 检查 package.json
  if [ ! -f "package.json" ]; then
    echo "⚠️  package.json 不存在，检查是否有其他位置..."
    
    # 检查是否有子目录包含 package.json
    FOUND_PACKAGE=$(find . -maxdepth 2 -name "package.json" -type f 2>/dev/null | head -1)
    
    if [ -n "$FOUND_PACKAGE" ]; then
      echo "✅ 找到 package.json: $FOUND_PACKAGE"
      # 如果 package.json 在子目录，切换到该目录
      PACKAGE_DIR=$(dirname "$FOUND_PACKAGE")
      if [ "$PACKAGE_DIR" != "." ]; then
        echo "   切换到目录: $PACKAGE_DIR"
        cd "$PACKAGE_DIR"
        SITE_DIR="$SITE_DIR/$PACKAGE_DIR"
      fi
    else
      echo "❌ 未找到 package.json，跳过此网站"
      echo "   请确保项目文件已上传到服务器"
      FAILED_SITES+=("$site (package.json 不存在)")
      continue
    fi
  fi
  
  echo "✅ package.json 存在"
  
  # 检查 node_modules
  if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install || {
      echo "❌ npm install 失败"
      FAILED_SITES+=("$site (npm install 失败)")
      continue
    }
  else
    echo "✅ node_modules 存在"
  fi
  
  # 构建项目
  if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
    echo "🔨 构建项目..."
    
    # 设置 Node.js 内存限制
    export NODE_OPTIONS="--max-old-space-size=3072"
    
    npm run build || {
      echo "❌ npm run build 失败"
      FAILED_SITES+=("$site (构建失败)")
      continue
    }
  else
    echo "✅ dist 目录已存在且不为空"
  fi
  
  # 验证 dist 目录
  if [ ! -d "dist" ] || [ -z "$(ls -A dist 2>/dev/null)" ]; then
    echo "❌ dist 目录不存在或为空"
    FAILED_SITES+=("$site (dist 目录无效)")
    continue
  fi
  
  DIST_SIZE=$(du -sh dist 2>/dev/null | cut -f1 || echo "未知")
  echo "✅ 构建完成，dist 大小: $DIST_SIZE"
  
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
set -e
DIST_DIR="$SITE_DIR/dist"
PORT=$port

if ! command -v serve >/dev/null 2>&1; then
  echo "错误: serve 命令未找到"
  exit 1
fi

if [ ! -d "\$DIST_DIR" ]; then
  echo "错误: dist 目录不存在: \$DIST_DIR"
  exit 1
fi

exec serve -s "\$DIST_DIR" -l "\$PORT" --no-clipboard
EOF
  
  chmod +x "$START_SCRIPT"
  echo "✅ 启动脚本已生成: $START_SCRIPT"
  
  # 使用 PM2 启动脚本
  echo "🚀 使用 PM2 启动前端服务..."
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
echo "📊 构建和启动结果汇总"
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

echo "端口监听状态:"
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir pm2_name <<< "${SITES[$site]}"
  PORT_STATUS=$(sudo netstat -tlnp 2>/dev/null | grep ":$port " || sudo ss -tlnp 2>/dev/null | grep ":$port " || echo "")
  if [ -n "$PORT_STATUS" ]; then
    echo "  ✅ 端口 $port ($site) 正在监听"
  else
    echo "  ❌ 端口 $port ($site) 未监听"
  fi
done
echo ""

echo "=========================================="
echo "✅ 构建和启动完成！"
echo "时间: $(date)"
echo "=========================================="

if [ ${#FAILED_SITES[@]} -gt 0 ]; then
  echo ""
  echo "⚠️  部分网站失败，请检查："
  echo "1. 项目文件是否已上传到服务器"
  echo "2. package.json 是否存在"
  echo "3. 构建日志: 查看各项目的日志文件"
  echo "4. PM2 日志: pm2 logs"
  exit 1
fi
