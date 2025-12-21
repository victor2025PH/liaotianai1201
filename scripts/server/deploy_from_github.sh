#!/bin/bash

# 从 GitHub 拉取最新代码并重新部署所有服务
# 使用方法: bash scripts/server/deploy_from_github.sh

set -e

echo "=========================================="
echo "🚀 从 GitHub 部署最新代码"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 1. 拉取最新代码
echo "1. 拉取最新代码..."
echo "----------------------------------------"
git fetch origin main || {
  echo "❌ Git fetch 失败"
  exit 1
}

# 检查是否有更新
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "✅ 代码已是最新版本"
else
  echo "发现新版本，拉取更新..."
  git pull origin main || {
    echo "❌ Git pull 失败"
    exit 1
  }
  echo "✅ 代码已更新"
fi
echo ""

# 2. 停止所有服务
echo "2. 停止所有服务..."
echo "----------------------------------------"
pm2 delete all 2>/dev/null || true

# 停止可能占用端口的进程
PORTS=(3000 3001 3002 3003 8000)
for PORT in "${PORTS[@]}"; do
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "停止占用端口 $PORT 的进程..."
    sudo lsof -ti :$PORT 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
    sleep 1
  fi
done

echo "✅ 所有服务已停止"
echo ""

# 3. 启动端口 3000 - saas-demo
echo "3. 启动端口 3000 - saas-demo..."
echo "----------------------------------------"
SAAS_DEMO_DIR="$PROJECT_ROOT/saas-demo"

if [ -d "$SAAS_DEMO_DIR" ] && [ -f "$SAAS_DEMO_DIR/package.json" ]; then
  cd "$SAAS_DEMO_DIR" || exit 1
  
  if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install || echo "⚠️  依赖安装失败，但继续..."
  fi
  
  if [ ! -d ".next" ]; then
    echo "构建 saas-demo..."
    npm run build || echo "⚠️  构建失败，但继续..."
  fi
  
  mkdir -p "$SAAS_DEMO_DIR/logs"
  pm2 start npm \
    --name saas-demo \
    --cwd "$SAAS_DEMO_DIR" \
    --error "$SAAS_DEMO_DIR/logs/saas-demo-error.log" \
    --output "$SAAS_DEMO_DIR/logs/saas-demo-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- start || echo "⚠️  saas-demo 启动失败"
  
  echo "✅ saas-demo 已启动 (端口 3000)"
else
  echo "⚠️  saas-demo 目录不存在"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 4. 启动端口 3001 - tgmini
echo "4. 启动端口 3001 - tgmini..."
echo "----------------------------------------"
TGMINI_DIR=$(find "$PROJECT_ROOT" -maxdepth 3 -type d -name "*tgmini*" 2>/dev/null | head -1)

if [ -n "$TGMINI_DIR" ] && [ -f "$TGMINI_DIR/package.json" ]; then
  cd "$TGMINI_DIR" || exit 1
  
  if [ ! -d "node_modules" ]; then
    npm install || echo "⚠️  依赖安装失败，但继续..."
  fi
  
  if [ ! -d "dist" ]; then
    echo "构建 tgmini..."
    npm run build || echo "⚠️  构建失败，但继续..."
  fi
  
  if [ -d "dist" ]; then
    pm2 start serve \
      --name tgmini-frontend \
      -- -s dist -l 3001 || echo "⚠️  tgmini-frontend 启动失败"
    echo "✅ tgmini-frontend 已启动 (端口 3001)"
  else
    echo "⚠️  未找到 dist 目录"
  fi
else
  echo "⚠️  未找到 tgmini 目录"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 5. 启动端口 3002 - hbwy/hongbao
echo "5. 启动端口 3002 - hbwy/hongbao..."
echo "----------------------------------------"
HBWY_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
  grep -iE "(hbwy|hongbao)" | head -1 | xargs dirname 2>/dev/null || echo "")

if [ -n "$HBWY_DIR" ] && [ -f "$HBWY_DIR/package.json" ]; then
  echo "找到 hbwy 目录: $HBWY_DIR"
  cd "$HBWY_DIR" || exit 1
  
  if [ ! -d "node_modules" ]; then
    npm install || echo "⚠️  依赖安装失败，但继续..."
  fi
  
  echo "构建 hbwy..."
  rm -rf dist build .next
  if npm run build 2>&1 | tee /tmp/hbwy_build.log; then
    if [ -d "dist" ]; then
      pm2 start serve \
        --name hongbao-frontend \
        -- -s dist -l 3002 || echo "⚠️  hongbao-frontend 启动失败"
      echo "✅ hongbao-frontend 已启动 (端口 3002)"
    else
      echo "❌ 构建成功但未找到 dist 目录"
      tail -20 /tmp/hbwy_build.log
    fi
  else
    echo "❌ 构建失败"
    tail -30 /tmp/hbwy_build.log | grep -A 5 "ERROR\|error" || tail -20 /tmp/hbwy_build.log
  fi
else
  echo "⚠️  未找到 hbwy/hongbao 目录"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 6. 启动端口 3003 - aizkw
echo "6. 启动端口 3003 - aizkw..."
echo "----------------------------------------"
AIZKW_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
  grep -iE "(aizkw|liaotian)" | \
  grep -v "/logs/" | \
  head -1 | xargs dirname 2>/dev/null || echo "")

if [ -n "$AIZKW_DIR" ] && [ -f "$AIZKW_DIR/package.json" ]; then
  echo "找到 aizkw 目录: $AIZKW_DIR"
  cd "$AIZKW_DIR" || exit 1
  
  if [ ! -d "node_modules" ]; then
    npm install || echo "⚠️  依赖安装失败，但继续..."
  fi
  
  if [ ! -d "dist" ]; then
    echo "构建 aizkw..."
    npm run build || echo "⚠️  构建失败，但继续..."
  fi
  
  if [ -d "dist" ]; then
    pm2 start serve \
      --name aizkw-frontend \
      -- -s dist -l 3003 || echo "⚠️  aizkw-frontend 启动失败"
    echo "✅ aizkw-frontend 已启动 (端口 3003)"
  else
    echo "⚠️  未找到 dist 目录"
  fi
else
  echo "⚠️  未找到 aizkw 目录"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 7. 等待服务启动
echo "7. 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 8. 保存 PM2 配置
pm2 save || true
echo "✅ PM2 配置已保存"
echo ""

# 9. 验证所有端口
echo "8. 验证所有端口..."
echo "----------------------------------------"
ALL_OK=true

for PORT in 3000 3001 3002 3003; do
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "✅ 端口 $PORT 正在监听"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
      echo "   ✅ HTTP 响应正常 (HTTP $HTTP_CODE)"
    else
      echo "   ⚠️  HTTP 响应异常 (HTTP $HTTP_CODE)"
      ALL_OK=false
    fi
  else
    echo "❌ 端口 $PORT 未监听"
    ALL_OK=false
  fi
done

echo ""
echo "PM2 进程列表："
pm2 list

echo ""
echo "=========================================="
if [ "$ALL_OK" = "true" ]; then
  echo "✅ 所有服务部署成功！"
else
  echo "⚠️  部分服务可能未正常启动"
fi
echo "时间: $(date)"
echo "=========================================="
