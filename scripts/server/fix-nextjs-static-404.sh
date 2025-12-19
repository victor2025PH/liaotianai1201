#!/bin/bash
# ============================================================
# 修复 Next.js 静态资源 404 问题
# ============================================================

echo "=========================================="
echo "🔧 修复 Next.js 静态资源 404 问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

cd "$FRONTEND_DIR" || exit 1

# 1. 检查构建产物
echo "[1/5] 检查构建产物..."
echo "----------------------------------------"
if [ -d ".next/static" ]; then
    STATIC_COUNT=$(find .next/static -type f 2>/dev/null | wc -l)
    echo "✅ .next/static 存在（包含 $STATIC_COUNT 个文件）"
    echo "示例文件:"
    find .next/static -type f | head -5
else
    echo "❌ .next/static 不存在，需要重新构建"
    exit 1
fi
echo ""

# 2. 检查 standalone 目录
echo "[2/5] 检查 standalone 目录..."
echo "----------------------------------------"
STANDALONE_DIR=".next/standalone"
if [ -d ".next/standalone/saas-demo" ]; then
    STANDALONE_DIR=".next/standalone/saas-demo"
    echo "发现嵌套的 standalone 目录: $STANDALONE_DIR"
fi

if [ ! -d "$STANDALONE_DIR" ]; then
    echo "❌ standalone 目录不存在"
    exit 1
fi

if [ ! -f "$STANDALONE_DIR/server.js" ]; then
    echo "❌ server.js 不存在"
    exit 1
fi

echo "✅ standalone 目录存在: $STANDALONE_DIR"
echo ""

# 3. 确保静态文件已复制
echo "[3/5] 确保静态文件已复制..."
echo "----------------------------------------"
mkdir -p "$STANDALONE_DIR/.next/static"
mkdir -p "$STANDALONE_DIR/.next/server"
mkdir -p "$STANDALONE_DIR/.next"

# 复制 BUILD_ID
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID "$STANDALONE_DIR/.next/BUILD_ID" 2>/dev/null || true
    echo "✅ BUILD_ID 已复制"
fi

# 复制所有 JSON 文件
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
    echo "复制 static 目录..."
    cp -r .next/static/* "$STANDALONE_DIR/.next/static/" 2>/dev/null || true
    STANDALONE_STATIC_COUNT=$(find "$STANDALONE_DIR/.next/static" -type f 2>/dev/null | wc -l)
    echo "✅ static 目录已复制（包含 $STANDALONE_STATIC_COUNT 个文件）"
    
    # 验证关键文件
    if [ -d "$STANDALONE_DIR/.next/static/chunks" ]; then
        CHUNK_COUNT=$(find "$STANDALONE_DIR/.next/static/chunks" -type f 2>/dev/null | wc -l)
        echo "✅ chunks 目录存在（包含 $CHUNK_COUNT 个文件）"
    else
        echo "❌ chunks 目录不存在"
    fi
else
    echo "❌ .next/static 目录不存在"
fi

# 复制 server 目录
if [ -d ".next/server" ]; then
    cp -r .next/server/* "$STANDALONE_DIR/.next/server/" 2>/dev/null || true
    SERVER_COUNT=$(find "$STANDALONE_DIR/.next/server" -type f 2>/dev/null | wc -l)
    echo "✅ server 目录已复制（包含 $SERVER_COUNT 个文件）"
else
    echo "⚠️  server 目录不存在"
fi

# 复制 public 目录
if [ -d "public" ]; then
    cp -r public "$STANDALONE_DIR/" 2>/dev/null || true
    echo "✅ public 目录已复制"
fi
echo ""

# 4. 验证文件路径
echo "[4/5] 验证文件路径..."
echo "----------------------------------------"
echo "检查 standalone 目录结构:"
ls -la "$STANDALONE_DIR/.next/" 2>/dev/null | head -10
echo ""

echo "检查 static 目录:"
ls -la "$STANDALONE_DIR/.next/static/" 2>/dev/null | head -10
echo ""

echo "检查 chunks 目录:"
if [ -d "$STANDALONE_DIR/.next/static/chunks" ]; then
    ls -la "$STANDALONE_DIR/.next/static/chunks/" 2>/dev/null | head -10
    echo "示例 chunk 文件:"
    find "$STANDALONE_DIR/.next/static/chunks" -name "*.js" | head -5
else
    echo "❌ chunks 目录不存在"
fi
echo ""

# 5. 重启前端服务
echo "[5/5] 重启前端服务..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1
sudo -u ubuntu pm2 restart frontend
sleep 5

echo "检查服务状态:"
sudo -u ubuntu pm2 list | grep frontend
echo ""

echo "测试静态资源访问:"
# 测试一个实际的 chunk 文件
CHUNK_FILE=$(find "$FRONTEND_DIR/$STANDALONE_DIR/.next/static/chunks" -name "*.js" 2>/dev/null | head -1)
if [ -n "$CHUNK_FILE" ]; then
    CHUNK_NAME=$(basename "$CHUNK_FILE")
    echo "测试文件: $CHUNK_NAME"
    
    # 测试直接访问
    DIRECT_TEST=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:3000/_next/static/chunks/$CHUNK_NAME" 2>/dev/null || echo "000")
    if [ "$DIRECT_TEST" = "200" ]; then
        echo "✅ 直接访问成功 (HTTP $DIRECT_TEST)"
    else
        echo "⚠️  直接访问返回: HTTP $DIRECT_TEST"
    fi
    
    # 测试通过 Nginx 访问（使用 /next/static，因为浏览器请求的是这个路径）
    NGINX_TEST=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/next/static/chunks/$CHUNK_NAME" 2>/dev/null || echo "000")
    if [ "$NGINX_TEST" = "200" ]; then
        echo "✅ 通过 Nginx 访问成功 (HTTP $NGINX_TEST)"
    else
        echo "⚠️  通过 Nginx 访问返回: HTTP $NGINX_TEST"
    fi
else
    echo "⚠️  未找到 chunk 文件进行测试"
fi
echo ""

echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "1. 前端日志: sudo -u ubuntu pm2 logs frontend --lines 50"
echo "2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "3. 静态文件路径: ls -la $FRONTEND_DIR/$STANDALONE_DIR/.next/static/chunks/"
echo ""

