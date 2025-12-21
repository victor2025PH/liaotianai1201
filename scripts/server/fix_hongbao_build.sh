#!/bin/bash

# 修复红包网站构建失败脚本
# 使用方法: bash scripts/server/fix_hongbao_build.sh

set -e

echo "=========================================="
echo "🔧 修复红包网站构建失败"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 查找红包项目目录
echo "1. 查找红包项目目录..."
echo "----------------------------------------"

HONGBAO_DIR=""
# 优先查找标准路径
if [ -d "$PROJECT_ROOT/react-vite-template/hbwy20251220" ] && [ -f "$PROJECT_ROOT/react-vite-template/hbwy20251220/package.json" ]; then
  HONGBAO_DIR="$PROJECT_ROOT/react-vite-template/hbwy20251220"
  echo "✅ 找到红包项目目录: $HONGBAO_DIR"
else
  # 查找包含 hbwy 或 hongbao 的目录
  HONGBAO_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
    grep -iE "(hbwy|hongbao)" | \
    grep -v "/\.git/" | \
    grep -v "/node_modules/" | \
    head -1 | xargs dirname 2>/dev/null || echo "")
  
  if [ -n "$HONGBAO_DIR" ] && [ -f "$HONGBAO_DIR/package.json" ]; then
    echo "✅ 找到红包项目目录: $HONGBAO_DIR"
  else
    echo "❌ 未找到红包项目目录"
    exit 1
  fi
fi

cd "$HONGBAO_DIR" || exit 1
echo ""

# 2. 检查并修复 Technical.tsx
echo "2. 检查 Technical.tsx 文件..."
echo "----------------------------------------"

TECHNICAL_FILE="$HONGBAO_DIR/components/Technical.tsx"
if [ ! -f "$TECHNICAL_FILE" ]; then
  # 尝试查找 Technical.tsx
  TECHNICAL_FILE=$(find "$HONGBAO_DIR" -name "Technical.tsx" -type f 2>/dev/null | head -1)
fi

if [ -z "$TECHNICAL_FILE" ] || [ ! -f "$TECHNICAL_FILE" ]; then
  echo "❌ 未找到 Technical.tsx 文件"
  exit 1
fi

echo "找到文件: $TECHNICAL_FILE"

# 检查是否有 JSX 语法错误（包含未转义的 > 符号）
if grep -q "remainingAmount > 0" "$TECHNICAL_FILE" 2>/dev/null; then
  echo "发现需要修复的 JSX 语法错误..."
  
  # 备份原文件
  cp "$TECHNICAL_FILE" "$TECHNICAL_FILE.bak"
  echo "✅ 已备份原文件: $TECHNICAL_FILE.bak"
  
  # 修复 > 符号为 HTML 实体
  sed -i "s/remainingAmount > 0/remainingAmount \&gt; 0/g" "$TECHNICAL_FILE"
  
  # 修复其他可能的 > 符号问题
  sed -i "s/{'>'}/{'\&gt;'}/g" "$TECHNICAL_FILE"
  
  echo "✅ Technical.tsx 已修复"
else
  echo "✅ Technical.tsx 无需修复"
fi

echo ""

# 3. 清理旧的构建
echo "3. 清理旧的构建..."
echo "----------------------------------------"
rm -rf dist build .next node_modules/.vite 2>/dev/null || true
echo "✅ 清理完成"
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
  echo "✅ node_modules 已存在，跳过安装"
fi
echo ""

# 5. 重新构建
echo "5. 重新构建项目..."
echo "----------------------------------------"
npm run build || {
  echo "❌ 构建失败"
  echo ""
  echo "构建错误详情："
  npm run build 2>&1 | tail -50
  exit 1
}
echo "✅ 构建完成"
echo ""

# 6. 重启服务
echo "6. 重启 hongbao-frontend 服务..."
echo "----------------------------------------"
cd "$PROJECT_ROOT" || exit 1

if pm2 list | grep -q "hongbao-frontend"; then
  pm2 restart hongbao-frontend || {
    echo "⚠️  PM2 restart 失败，尝试删除后重新启动..."
    pm2 delete hongbao-frontend 2>/dev/null || true
    
    # 确定构建输出目录
    BUILD_DIR=""
    if [ -d "$HONGBAO_DIR/dist" ]; then
      BUILD_DIR="dist"
    elif [ -d "$HONGBAO_DIR/build" ]; then
      BUILD_DIR="build"
    fi
    
    if [ -n "$BUILD_DIR" ]; then
      pm2 start serve \
        --name hongbao-frontend \
        -- -s "$HONGBAO_DIR/$BUILD_DIR" -l 3002 || {
        echo "❌ 服务启动失败"
        exit 1
      }
      echo "✅ hongbao-frontend 已重新启动"
    else
      echo "❌ 未找到构建输出目录"
      exit 1
    fi
  }
  echo "✅ hongbao-frontend 已重启"
else
  echo "⚠️  PM2 中未找到 hongbao-frontend 进程，尝试启动..."
  
  BUILD_DIR=""
  if [ -d "$HONGBAO_DIR/dist" ]; then
    BUILD_DIR="dist"
  elif [ -d "$HONGBAO_DIR/build" ]; then
    BUILD_DIR="build"
  fi
  
  if [ -n "$BUILD_DIR" ]; then
    pm2 start serve \
      --name hongbao-frontend \
      -- -s "$HONGBAO_DIR/$BUILD_DIR" -l 3002 || {
      echo "❌ 服务启动失败"
      exit 1
    }
    echo "✅ hongbao-frontend 已启动"
  else
    echo "❌ 未找到构建输出目录"
    exit 1
  fi
fi

echo ""

# 7. 等待服务启动
echo "7. 等待服务启动..."
echo "----------------------------------------"
sleep 5

# 8. 检查状态
echo "8. 检查服务状态..."
echo "----------------------------------------"
pm2 list | grep hongbao-frontend || echo "⚠️  未找到 hongbao-frontend 进程"

echo ""
echo "服务日志（最近 20 行）："
echo "----------------------------------------"
pm2 logs hongbao-frontend --lines 20 --nostream || {
  echo "⚠️  无法获取日志"
}

echo ""
echo "测试端口 3002..."
echo "----------------------------------------"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3002 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
  echo "✅ 端口 3002 HTTP 响应正常 (HTTP $HTTP_CODE)"
else
  echo "⚠️  端口 3002 HTTP 响应异常 (HTTP $HTTP_CODE)"
fi

echo ""
echo "=========================================="
echo "✅ 红包网站修复完成！"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查："
echo "  pm2 logs hongbao-frontend"
echo "  pm2 describe hongbao-frontend"
