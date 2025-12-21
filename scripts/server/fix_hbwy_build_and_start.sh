#!/bin/bash

# 修复 hbwy 项目并启动（端口 3002）
# 使用方法: bash scripts/server/fix_hbwy_build_and_start.sh

set -e

echo "=========================================="
echo "🔧 修复 hbwy 项目并启动（端口 3002）"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

# 1. 修复 Technical.tsx
echo "1. 修复 Technical.tsx..."
echo "----------------------------------------"
bash scripts/server/fix_technical_tsx_final.sh || {
  echo "⚠️  JSX 修复失败，但继续..."
}
echo ""

# 2. 查找 hbwy 项目目录
echo "2. 查找 hbwy 项目目录..."
echo "----------------------------------------"
HBWY_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
  grep -iE "(hbwy|hongbao)" | head -1 | xargs dirname 2>/dev/null || echo "")

if [ -z "$HBWY_DIR" ]; then
  echo "❌ 未找到 hbwy 项目目录"
  exit 1
fi

echo "找到 hbwy 目录: $HBWY_DIR"
cd "$HBWY_DIR" || exit 1

# 3. 检查并修复 Technical.tsx（再次确保）
echo "3. 检查 Technical.tsx..."
echo "----------------------------------------"
TECHNICAL_FILE=$(find . -name "Technical.tsx" 2>/dev/null | head -1)

if [ -n "$TECHNICAL_FILE" ]; then
  echo "找到 Technical.tsx: $TECHNICAL_FILE"
  
  # 检查是否还有 HTML 实体
  if grep -q "&lt;\|&gt;" "$TECHNICAL_FILE" 2>/dev/null; then
    echo "发现 HTML 实体，修复..."
    sed -i 's/&lt;/</g' "$TECHNICAL_FILE"
    sed -i 's/&gt;/>/g' "$TECHNICAL_FILE"
  fi
  
  # 检查是否还有问题语法
  if grep -q 'require(<span' "$TECHNICAL_FILE" 2>/dev/null; then
    echo "修复 require 语句..."
    sed -i 's/require(<span[^>]*>\([^<]*\)<\/span>, "\([^"]*\)");/require(`\1`, "\2");/g' "$TECHNICAL_FILE"
  fi
  
  if grep -q '<span[^>]*>emit</span>' "$TECHNICAL_FILE" 2>/dev/null; then
    echo "修复 emit 语句..."
    sed -i 's/<span[^>]*>emit<\/span>/emit/g' "$TECHNICAL_FILE"
  fi
  
  echo "✅ Technical.tsx 已修复"
else
  echo "⚠️  未找到 Technical.tsx"
fi
echo ""

# 4. 安装依赖
echo "4. 安装依赖..."
echo "----------------------------------------"
if [ ! -d "node_modules" ]; then
  npm install || {
    echo "❌ 依赖安装失败"
    exit 1
  }
  echo "✅ 依赖安装完成"
else
  echo "✅ node_modules 已存在"
fi
echo ""

# 5. 清理旧构建
echo "5. 清理旧构建..."
echo "----------------------------------------"
rm -rf dist build .next
echo "✅ 旧构建已清理"
echo ""

# 6. 构建项目
echo "6. 构建项目..."
echo "----------------------------------------"
if npm run build 2>&1 | tee /tmp/hbwy_build.log; then
  echo "✅ 构建命令执行完成"
  
  # 检查构建输出目录
  BUILD_DIR=""
  if [ -d "dist" ]; then
    BUILD_DIR="dist"
  elif [ -d "build" ]; then
    BUILD_DIR="build"
  elif [ -d ".next" ]; then
    BUILD_DIR=".next"
  elif [ -d ".next/standalone" ]; then
    BUILD_DIR=".next/standalone"
  fi
  
  if [ -n "$BUILD_DIR" ]; then
    echo "✅ 找到构建输出目录: $BUILD_DIR"
  else
    echo "❌ 未找到构建输出目录"
    echo "构建日志："
    tail -30 /tmp/hbwy_build.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/hbwy_build.log
    exit 1
  fi
else
  echo "❌ 构建失败"
  echo "构建错误："
  tail -30 /tmp/hbwy_build.log | grep -A 5 "ERROR\|error\|failed" || tail -20 /tmp/hbwy_build.log
  exit 1
fi
echo ""

# 7. 停止端口 3002 上的旧进程
echo "7. 停止端口 3002 上的旧进程..."
echo "----------------------------------------"
if lsof -i :3002 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":3002 "; then
  PIDS=$(lsof -ti :3002 2>/dev/null || ss -tlnp 2>/dev/null | grep ":3002 " | grep -oP "pid=\K\d+" || echo "")
  for PID in $PIDS; do
    sudo kill -9 $PID 2>/dev/null || true
  done
  sleep 1
fi

pm2 delete hongbao-frontend 2>/dev/null || true
echo "✅ 端口 3002 已清理"
echo ""

# 8. 启动服务
echo "8. 启动服务..."
echo "----------------------------------------"
if [ "$BUILD_DIR" = "dist" ] || [ "$BUILD_DIR" = "build" ]; then
  # 使用 serve 启动静态文件
  pm2 start serve \
    --name hongbao-frontend \
    -- -s "$BUILD_DIR" -l 3002 || {
    echo "❌ 启动失败"
    exit 1
  }
  echo "✅ hongbao-frontend 已启动 (端口 3002)"
elif [ "$BUILD_DIR" = ".next" ] || [ "$BUILD_DIR" = ".next/standalone" ]; then
  # 使用 npm start 启动 Next.js
  pm2 start npm \
    --name hongbao-frontend \
    --cwd "$HBWY_DIR" \
    -- start -- -p 3002 || {
    echo "❌ 启动失败"
    exit 1
  }
  echo "✅ hongbao-frontend 已启动 (端口 3002)"
else
  echo "❌ 无法确定启动方式"
  exit 1
fi

pm2 save || true
echo ""

# 9. 验证
echo "9. 验证服务..."
echo "----------------------------------------"
sleep 5

if lsof -i :3002 >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":3002 "; then
  echo "✅ 端口 3002 正在监听"
  
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3002 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo "✅ HTTP 响应正常 (HTTP $HTTP_CODE)"
  else
    echo "⚠️  HTTP 响应异常 (HTTP $HTTP_CODE)"
  fi
else
  echo "❌ 端口 3002 未监听"
  pm2 logs hongbao-frontend --lines 20 --nostream 2>/dev/null || true
  exit 1
fi

echo ""
echo "=========================================="
echo "✅ hbwy 项目修复并启动成功！"
echo "时间: $(date)"
echo "=========================================="
