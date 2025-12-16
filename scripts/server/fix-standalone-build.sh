#!/bin/bash
# ============================================================
# Fix Next.js Standalone Build (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Diagnose and fix Next.js standalone build issues
#
# One-click execution: sudo bash scripts/server/fix-standalone-build.sh
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "============================================================"
echo "🔍 Next.js Standalone 构建诊断和修复"
echo "============================================================"
echo ""

cd "$FRONTEND_DIR" || {
  echo "❌ 无法进入前端目录: $FRONTEND_DIR"
  exit 1
}

echo "[1/5] 检查当前构建状态"
echo "----------------------------------------"
echo "检查 .next 目录..."
if [ -d ".next" ]; then
  echo "✅ .next 目录存在"
  echo "目录内容:"
  ls -la .next/ | head -10
else
  echo "❌ .next 目录不存在，需要重新构建"
fi

echo ""
echo "查找 server.js 文件..."
SERVER_JS=$(find .next -name "server.js" -type f 2>/dev/null | head -1)
if [ -n "$SERVER_JS" ]; then
  echo "✅ 找到 server.js: $SERVER_JS"
  ls -la "$SERVER_JS"
else
  echo "❌ 未找到 server.js 文件"
fi

echo ""
echo "检查 standalone 目录..."
if [ -d ".next/standalone" ]; then
  echo "✅ standalone 目录存在"
  echo "standalone 目录结构:"
  find .next/standalone -type f | head -20
  echo ""
  echo "standalone 目录树:"
  tree .next/standalone -L 3 2>/dev/null || find .next/standalone -type d | head -20
else
  echo "❌ standalone 目录不存在"
fi

echo ""
echo "[2/5] 检查 Next.js 配置"
echo "----------------------------------------"
if grep -q "output.*standalone" next.config.ts 2>/dev/null || grep -q '"output".*"standalone"' next.config.js 2>/dev/null; then
  echo "✅ standalone 输出已配置"
  grep -A 1 "output" next.config.ts 2>/dev/null || grep -A 1 "output" next.config.js 2>/dev/null || true
else
  echo "❌ standalone 输出未配置"
  echo "需要在 next.config.ts 中添加: output: 'standalone'"
fi

echo ""
echo "[3/5] 清理并重新构建"
echo "----------------------------------------"
echo "停止前端服务..."
sudo systemctl stop liaotian-frontend 2>/dev/null || true

echo "清理旧的构建产物..."
rm -rf .next/standalone
echo "✅ 已清理 standalone 目录"

echo ""
echo "开始重新构建..."
export NODE_ENV=production
export NODE_OPTIONS="--max-old-space-size=4096"
export NEXT_TELEMETRY_DISABLED=1

# 执行构建并捕获输出
BUILD_OUTPUT=$(npm run build 2>&1)
BUILD_EXIT_CODE=$?

echo "$BUILD_OUTPUT" | tail -30

if [ $BUILD_EXIT_CODE -ne 0 ]; then
  echo "❌ 构建失败，退出码: $BUILD_EXIT_CODE"
  echo "构建日志已保存到 /tmp/nextjs-build-error.log"
  echo "$BUILD_OUTPUT" > /tmp/nextjs-build-error.log
  exit 1
fi

echo ""
echo "[4/5] 验证构建产物"
echo "----------------------------------------"
# 再次查找 server.js
SERVER_JS=$(find .next -name "server.js" -type f 2>/dev/null | head -1)

if [ -n "$SERVER_JS" ]; then
  echo "✅ 找到 server.js: $SERVER_JS"
  ls -la "$SERVER_JS"
  
  # 检查文件大小（应该 > 0）
  FILE_SIZE=$(stat -f%z "$SERVER_JS" 2>/dev/null || stat -c%s "$SERVER_JS" 2>/dev/null || echo "0")
  if [ "$FILE_SIZE" -gt 0 ]; then
    echo "✅ server.js 文件大小: $FILE_SIZE 字节"
  else
    echo "⚠️  server.js 文件大小为 0，可能有问题"
  fi
else
  echo "❌ 构建完成但未找到 server.js"
  echo ""
  echo "检查 standalone 目录内容:"
  if [ -d ".next/standalone" ]; then
    find .next/standalone -type f | head -20
    echo ""
    echo "检查是否有嵌套的项目目录:"
    find .next/standalone -type d -name "saas-demo" -o -name "telegram-ai-system" 2>/dev/null | head -5
  fi
  exit 1
fi

echo ""
echo "[5/5] 修复服务配置（如果需要）"
echo "----------------------------------------"
# 如果 server.js 不在预期的位置，需要更新服务配置
EXPECTED_PATH="$FRONTEND_DIR/.next/standalone/server.js"
if [ "$SERVER_JS" != "$EXPECTED_PATH" ]; then
  echo "⚠️  server.js 不在预期位置"
  echo "预期: $EXPECTED_PATH"
  echo "实际: $SERVER_JS"
  echo ""
  echo "需要更新 systemd 服务配置中的路径"
  echo "当前服务配置:"
  sudo systemctl cat liaotian-frontend | grep -E "ExecStart|WorkingDirectory" || true
else
  echo "✅ server.js 在预期位置"
fi

echo ""
echo "============================================================"
echo "✅ 诊断完成"
echo "============================================================"
echo ""
echo "如果 server.js 已找到，可以启动服务:"
echo "  sudo systemctl start liaotian-frontend"
echo "  sudo systemctl status liaotian-frontend"
echo ""

