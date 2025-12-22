#!/bin/bash
# ============================================================
# 修复并启动三个网站
# ============================================================

set -e

PROJECT_ROOT="/home/***/telegram-ai-system"

echo "=========================================="
echo "🔧 修复并启动三个网站"
echo "时间: $(date)"
echo "=========================================="
echo ""

# 定义网站配置
declare -A SITES=(
  ["tgmini"]="3001:tgmini20251220:tgmini-frontend:tgmini.usdt2026.cc"
  ["hongbao"]="3002:hbwy20251220:hongbao-frontend:hongbao.usdt2026.cc"
  ["aizkw"]="3003:aizkw20251219:aizkw-frontend:aizkw.usdt2026.cc"
)

# 检查并安装 serve
if ! command -v serve >/dev/null 2>&1; then
  echo "📦 安装 serve..."
  sudo npm install -g serve
fi

# 处理每个网站
for site in "${!SITES[@]}"; do
  IFS=':' read -r port dir pm2_name domain <<< "${SITES[$site]}"
  
  echo "=========================================="
  echo "处理 $site (端口 $port)"
  echo "=========================================="
  
  PROJECT_DIR="$PROJECT_ROOT/$dir"
  
  # 检查目录是否存在
  if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 目录不存在: $PROJECT_DIR"
    echo "跳过 $site"
    echo ""
    continue
  fi
  
  cd "$PROJECT_DIR" || {
    echo "❌ 无法进入目录: $PROJECT_DIR"
    continue
  }
  
  # 1. 安装依赖
  echo "[1/5] 安装依赖..."
  if [ ! -d "node_modules" ]; then
    npm install --legacy-peer-deps || {
      echo "⚠️  依赖安装失败，但继续..."
    }
  else
    echo "  ✅ node_modules 已存在"
  fi
  
  # 2. 构建项目
  echo "[2/5] 构建项目..."
  if [ ! -d "dist" ]; then
    export NODE_OPTIONS="--max-old-space-size=3072"
    npm run build || {
      echo "❌ 构建失败"
      echo "跳过 $site"
      echo ""
      continue
    }
  else
    echo "  ✅ dist 目录已存在"
  fi
  
  # 3. 停止旧进程
  echo "[3/5] 停止旧进程..."
  pm2 delete "$pm2_name" 2>/dev/null || true
  if sudo lsof -i :$port >/dev/null 2>&1; then
    sudo lsof -ti :$port | xargs sudo kill -9 2>/dev/null || true
    sleep 2
  fi
  
  # 4. 启动服务
  echo "[4/5] 启动服务 (端口 $port)..."
  mkdir -p "$PROJECT_ROOT/logs"
  pm2 start serve \
    --name "$pm2_name" \
    --max-memory-restart 1G \
    --error "$PROJECT_ROOT/logs/${pm2_name}-error.log" \
    --output "$PROJECT_ROOT/logs/${pm2_name}-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- -s "$PROJECT_DIR/dist" -l $port || {
    echo "❌ PM2 启动失败"
    pm2 logs "$pm2_name" --lines 20 --nostream 2>/dev/null || true
    continue
  }
  
  pm2 save || true
  
  # 5. 等待端口启动
  echo "[5/5] 等待服务启动..."
  RETRIES=0
  MAX_RETRIES=20
  while ! nc -z 127.0.0.1 $port 2>/dev/null; do
    sleep 1
    RETRIES=$((RETRIES+1))
    if [ $RETRIES -ge $MAX_RETRIES ]; then
      echo "⚠️  端口 $port 启动超时"
      break
    fi
  done
  
  if nc -z 127.0.0.1 $port 2>/dev/null; then
    echo "  ✅ $site 已成功启动 (端口 $port)"
  else
    echo "  ❌ $site 启动失败"
  fi
  
  echo ""
done

# 保存 PM2 状态
pm2 save || true

# 显示最终状态
echo "=========================================="
echo "📊 最终状态"
echo "=========================================="
pm2 list
echo ""

echo "端口监听状态:"
netstat -tlnp | grep -E "3001|3002|3003" || echo "没有服务在监听"
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
