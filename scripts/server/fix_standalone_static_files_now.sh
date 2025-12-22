#!/bin/bash
# ============================================================
# 立即修复 Next.js standalone 模式静态文件缺失问题
# 无需重新构建，直接复制静态文件并重启服务
# ============================================================

set -e

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_ROOT/saas-demo"

echo "=========================================="
echo "🔧 立即修复 Next.js standalone 静态文件"
echo "=========================================="
echo ""

cd "$FRONTEND_DIR" || exit 1

# 1. 检查构建输出
echo "[1/4] 检查构建输出..."
echo "----------------------------------------"
if [ ! -d ".next/static" ]; then
  echo "❌ .next/static 不存在，需要重新构建"
  exit 1
fi

STATIC_COUNT=$(find .next/static -type f 2>/dev/null | wc -l)
echo "✅ .next/static 存在（$STATIC_COUNT 个文件）"

if [ ! -d ".next/standalone" ]; then
  echo "❌ .next/standalone 不存在，需要重新构建"
  exit 1
fi
echo "✅ .next/standalone 存在"
echo ""

# 2. 确定 standalone 目录路径
echo "[2/4] 确定 standalone 目录路径..."
echo "----------------------------------------"
STANDALONE_DIR=".next/standalone"
if [ -d ".next/standalone/saas-demo" ]; then
  STANDALONE_DIR=".next/standalone/saas-demo"
  echo "发现嵌套的 standalone 目录: $STANDALONE_DIR"
else
  echo "使用标准 standalone 目录: $STANDALONE_DIR"
fi

if [ ! -f "$STANDALONE_DIR/server.js" ]; then
  echo "❌ server.js 不存在: $STANDALONE_DIR/server.js"
  exit 1
fi
echo "✅ server.js 存在"
echo ""

# 3. 复制静态文件
echo "[3/4] 复制静态文件到 standalone 目录..."
echo "----------------------------------------"

# 确保目录结构完整
mkdir -p "$STANDALONE_DIR/.next/static"
mkdir -p "$STANDALONE_DIR/.next/server"
mkdir -p "$STANDALONE_DIR/.next"

# 复制 BUILD_ID
if [ -f ".next/BUILD_ID" ]; then
  cp .next/BUILD_ID "$STANDALONE_DIR/.next/BUILD_ID" 2>/dev/null || true
  echo "✅ BUILD_ID 已复制"
fi

# 复制所有 JSON 配置文件
JSON_COUNT=0
for json_file in .next/*.json; do
  if [ -f "$json_file" ]; then
    cp "$json_file" "$STANDALONE_DIR/.next/" 2>/dev/null || true
    JSON_COUNT=$((JSON_COUNT + 1))
  fi
done
echo "✅ 已复制 $JSON_COUNT 个 JSON 配置文件"

# 复制 static 目录（关键！）
if [ -d ".next/static" ]; then
  echo "复制 .next/static 目录..."
  rm -rf "$STANDALONE_DIR/.next/static"/* 2>/dev/null || true
  cp -r .next/static/* "$STANDALONE_DIR/.next/static/" 2>/dev/null || true
  STANDALONE_STATIC_COUNT=$(find "$STANDALONE_DIR/.next/static" -type f 2>/dev/null | wc -l)
  echo "✅ 已复制 $STANDALONE_STATIC_COUNT 个静态文件"
  
  # 验证 chunks 目录
  if [ -d "$STANDALONE_DIR/.next/static/chunks" ]; then
    CHUNK_COUNT=$(find "$STANDALONE_DIR/.next/static/chunks" -type f 2>/dev/null | wc -l)
    echo "✅ chunks 目录存在（$CHUNK_COUNT 个文件）"
  else
    echo "❌ chunks 目录不存在，复制可能失败"
    exit 1
  fi
else
  echo "❌ .next/static 目录不存在"
  exit 1
fi

# 复制 server 目录
if [ -d ".next/server" ]; then
  echo "复制 .next/server 目录..."
  rm -rf "$STANDALONE_DIR/.next/server"/* 2>/dev/null || true
  cp -r .next/server/* "$STANDALONE_DIR/.next/server/" 2>/dev/null || true
  SERVER_COUNT=$(find "$STANDALONE_DIR/.next/server" -type f 2>/dev/null | wc -l)
  echo "✅ 已复制 $SERVER_COUNT 个服务器文件"
else
  echo "⚠️  .next/server 目录不存在"
fi

# 复制 public 目录
if [ -d "public" ]; then
  cp -r public "$STANDALONE_DIR/" 2>/dev/null || true
  echo "✅ public 目录已复制"
fi
echo ""

# 4. 重启服务
echo "[4/4] 重启 Next.js 服务..."
echo "----------------------------------------"

# 停止旧进程
pm2 delete saas-demo-frontend 2>/dev/null || true
sleep 2

# 启动服务（使用正确的目录）
pm2 start node \
  --name saas-demo-frontend \
  --max-memory-restart 1G \
  --cwd "$(pwd)/$STANDALONE_DIR" \
  --error "$PROJECT_ROOT/logs/saas-demo-frontend-error.log" \
  --output "$PROJECT_ROOT/logs/saas-demo-frontend-out.log" \
  --merge-logs \
  --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
  -- server.js || {
  echo "❌ PM2 启动失败"
  exit 1
}

pm2 save || true
sleep 3

# 验证服务状态
if pm2 list | grep -q "saas-demo-frontend.*online"; then
  echo "✅ Next.js 服务已启动"
  
  # 测试静态文件访问
  SAMPLE_FILE=$(find "$STANDALONE_DIR/.next/static/chunks" -name "*.js" -type f 2>/dev/null | head -1)
  if [ -n "$SAMPLE_FILE" ]; then
    REL_PATH=${SAMPLE_FILE#${STANDALONE_DIR}/.next/static/}
    TEST_URL="http://127.0.0.1:3000/_next/static/$REL_PATH"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$TEST_URL" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
      echo "✅ 静态文件可以正常访问 (HTTP $HTTP_CODE)"
    else
      echo "⚠️  静态文件访问异常 (HTTP $HTTP_CODE)"
    fi
  fi
else
  echo "❌ Next.js 服务启动失败"
  pm2 logs saas-demo-frontend --lines 20 --nostream
  exit 1
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "建议操作："
echo "1. 清除浏览器缓存并刷新页面"
echo "2. 如果还有问题，检查日志: pm2 logs saas-demo-frontend --lines 50"
