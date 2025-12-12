#!/bin/bash
# ============================================================
# 强制重新构建前端
# ============================================================

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ Project directory not found: $PROJECT_DIR"
  exit 1
fi

cd "$PROJECT_DIR"

if [ ! -d "saas-demo" ]; then
  echo "❌ Frontend directory not found: saas-demo"
  exit 1
fi

echo "=========================================="
echo "强制重新构建前端"
echo "=========================================="
echo ""

cd saas-demo

# 清理旧的构建
echo "[1/4] 清理旧的构建文件..."
rm -rf .next
rm -rf node_modules/.cache
echo "✅ 清理完成"

# 安装依赖
echo ""
echo "[2/4] 安装依赖..."
export NODE_OPTIONS="--max-old-space-size=2048"
timeout 20m npm install --prefer-offline --no-audit --no-fund || {
  echo "⚠️  依赖安装失败或超时"
  exit 1
}
echo "✅ 依赖安装完成"

# 构建前端
echo ""
echo "[3/4] 构建前端..."
timeout 20m npm run build || {
  echo "❌ 构建失败或超时"
  exit 1
}
echo "✅ 构建完成"

# 准备standalone目录
echo ""
echo "[4/4] 准备standalone目录..."
if [ -d ".next/standalone" ]; then
  # 复制public目录
  if [ -d "public" ]; then
    cp -r public .next/standalone/ || true
  fi
  
  # 确保.next目录存在
  mkdir -p .next/standalone/.next
  
  # 复制static目录
  if [ -d ".next/static" ]; then
    rm -rf .next/standalone/.next/static
    cp -r .next/static .next/standalone/.next/ || {
      echo "❌ 复制static目录失败"
      exit 1
    }
  fi
  
  # 验证关键文件
  if [ ! -f ".next/standalone/server.js" ]; then
    echo "❌ server.js not found"
    exit 1
  fi
  
  echo "✅ Standalone目录准备完成"
else
  echo "❌ .next/standalone目录不存在"
  exit 1
fi

# 重启前端服务
echo ""
echo "重启前端服务..."
FRONTEND_SERVICE=""
if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
  FRONTEND_SERVICE="liaotian-frontend"
elif systemctl cat smart-tg-frontend.service >/dev/null 2>&1; then
  FRONTEND_SERVICE="smart-tg-frontend"
fi

if [ -n "$FRONTEND_SERVICE" ]; then
  sudo systemctl restart "$FRONTEND_SERVICE"
  sleep 5
  if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务已重启"
  else
    echo "⚠️  前端服务重启失败，查看日志: sudo journalctl -u $FRONTEND_SERVICE -n 50"
  fi
else
  echo "⚠️  前端服务未找到"
fi

echo ""
echo "=========================================="
echo "✅ 前端重新构建完成！"
echo "=========================================="

