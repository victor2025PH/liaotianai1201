#!/bin/bash
# ============================================================
# 修复前端缺失的文件（BUILD_ID、JSON 文件、server 目录等）
# ============================================================

echo "=========================================="
echo "🔧 修复前端缺失的文件"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

cd "$FRONTEND_DIR" || exit 1

# 1. 停止前端服务
echo "[1/4] 停止前端服务..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop frontend 2>/dev/null || true
sleep 2
echo "✅ 前端服务已停止"
echo ""

# 2. 检查 standalone 目录
echo "[2/4] 检查 standalone 目录..."
echo "----------------------------------------"
STANDALONE_DIR=".next/standalone"
if [ ! -d "$STANDALONE_DIR" ]; then
    echo "❌ standalone 目录不存在，需要重新构建"
    exit 1
fi

# 检查是否有嵌套的项目目录
if [ -d "$STANDALONE_DIR/saas-demo" ]; then
    STANDALONE_DIR="$STANDALONE_DIR/saas-demo"
    echo "发现嵌套的 standalone 目录: $STANDALONE_DIR"
fi

echo "✅ standalone 目录: $STANDALONE_DIR"
echo ""

# 3. 复制所有必需的文件
echo "[3/4] 复制所有必需的文件..."
echo "----------------------------------------"

# 确保目录存在
mkdir -p "$STANDALONE_DIR/.next/static"
mkdir -p "$STANDALONE_DIR/.next/server"
mkdir -p "$STANDALONE_DIR/.next"

# 复制 BUILD_ID
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID "$STANDALONE_DIR/.next/BUILD_ID" 2>/dev/null || true
    echo "✅ BUILD_ID 已复制"
else
    echo "⚠️  BUILD_ID 不存在"
fi

# 复制所有 JSON 配置文件
JSON_COUNT=0
for json_file in .next/*.json; do
    if [ -f "$json_file" ]; then
        cp "$json_file" "$STANDALONE_DIR/.next/" 2>/dev/null || true
        JSON_COUNT=$((JSON_COUNT + 1))
    fi
done
if [ $JSON_COUNT -gt 0 ]; then
    echo "✅ 已复制 $JSON_COUNT 个 JSON 配置文件"
else
    echo "⚠️  未找到 JSON 配置文件"
fi

# 复制 static 目录
if [ -d ".next/static" ]; then
    cp -r .next/static/* "$STANDALONE_DIR/.next/static/" 2>/dev/null || true
    STATIC_COUNT=$(find "$STANDALONE_DIR/.next/static" -type f 2>/dev/null | wc -l)
    echo "✅ static 目录已复制（包含 $STATIC_COUNT 个文件）"
else
    echo "⚠️  static 目录不存在"
fi

# 复制 server 目录（关键：包含 pages-manifest.json 等）
if [ -d ".next/server" ]; then
    cp -r .next/server/* "$STANDALONE_DIR/.next/server/" 2>/dev/null || true
    SERVER_COUNT=$(find "$STANDALONE_DIR/.next/server" -type f 2>/dev/null | wc -l)
    echo "✅ server 目录已复制（包含 $SERVER_COUNT 个文件）"
    
    # 验证关键文件
    if [ -f "$STANDALONE_DIR/.next/server/pages-manifest.json" ]; then
        echo "✅ pages-manifest.json 存在"
    else
        echo "⚠️  pages-manifest.json 不存在"
    fi
else
    echo "❌ server 目录不存在"
fi

# 复制 public 目录
if [ -d "public" ]; then
    cp -r public "$STANDALONE_DIR/" 2>/dev/null || true
    echo "✅ public 目录已复制"
fi

echo ""

# 4. 验证并重启服务
echo "[4/4] 验证文件并重启服务..."
echo "----------------------------------------"

# 验证关键文件
MISSING_FILES=0
if [ ! -f "$STANDALONE_DIR/server.js" ]; then
    echo "❌ server.js 不存在"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ ! -f "$STANDALONE_DIR/.next/BUILD_ID" ]; then
    echo "⚠️  BUILD_ID 不存在"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ ! -f "$STANDALONE_DIR/.next/server/pages-manifest.json" ]; then
    echo "⚠️  pages-manifest.json 不存在"
    MISSING_FILES=$((MISSING_FILES + 1))
fi

if [ $MISSING_FILES -eq 0 ]; then
    echo "✅ 所有关键文件存在"
    
    # 重启前端服务
    cd "$PROJECT_DIR" || exit 1
    sudo -u ubuntu pm2 restart frontend
    sleep 5
    
    # 检查状态
    FRONTEND_STATUS=$(sudo -u ubuntu pm2 list | grep frontend | awk '{print $10}' || echo "")
    if [ "$FRONTEND_STATUS" = "online" ]; then
        echo "✅ Frontend 服务已重启并运行正常"
    else
        echo "❌ Frontend 服务重启失败，状态: $FRONTEND_STATUS"
        echo "查看错误日志:"
        sudo -u ubuntu pm2 logs frontend --err --lines 10 --nostream 2>&1 | tail -10
    fi
else
    echo "❌ 缺少关键文件，无法重启服务"
    echo "请重新构建前端: cd $FRONTEND_DIR && npm run build"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="

