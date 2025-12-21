#!/bin/bash

# 修复权限并构建所有项目
# 使用方法: sudo bash scripts/server/fix_permissions_and_build.sh

set -e

echo "=========================================="
echo "🔧 修复权限并构建所有项目"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"

# 确保在正确的目录
if [ ! -d "$PROJECT_ROOT" ]; then
  echo "❌ 项目根目录不存在: $PROJECT_ROOT"
  exit 1
fi

cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目根目录"
  exit 1
}

echo "✅ 当前目录: $(pwd)"
echo ""

# 修复权限（确保 ubuntu 用户拥有所有文件）
echo "=========================================="
echo "🔐 修复文件权限..."
echo "=========================================="
echo ""

# 修复项目根目录权限
chown -R ubuntu:ubuntu "$PROJECT_ROOT" || {
  echo "⚠️  权限修复失败，继续执行..."
}

# 修复三个项目的权限
for project_dir in aizkw20251219 hbwy20251220 tgmini20251220; do
  project_path="$PROJECT_ROOT/$project_dir"
  
  if [ -d "$project_path" ]; then
    echo "修复权限: $project_dir"
    chown -R ubuntu:ubuntu "$project_path" || true
    chmod -R u+w "$project_path" || true
  else
    echo "⚠️  项目目录不存在: $project_path"
  fi
done

echo ""
echo "✅ 权限修复完成"
echo ""

# 安装依赖并构建
echo "=========================================="
echo "📦 安装依赖并构建项目..."
echo "=========================================="
echo ""

declare -A PROJECTS=(
  ["aizkw"]="aizkw20251219"
  ["hongbao"]="hbwy20251220"
  ["tgmini"]="tgmini20251220"
)

for project_name in "${!PROJECTS[@]}"; do
  project_dir="${PROJECTS[$project_name]}"
  project_path="$PROJECT_ROOT/$project_dir"
  
  echo "=========================================="
  echo "📁 处理项目: $project_name"
  echo "目录: $project_path"
  echo "=========================================="
  echo ""
  
  if [ ! -d "$project_path" ]; then
    echo "❌ 项目目录不存在: $project_path"
    echo "跳过此项目"
    echo ""
    continue
  fi
  
  # 进入项目目录
  cd "$project_path" || {
    echo "❌ 无法进入项目目录"
    continue
  }
  
  echo "当前目录: $(pwd)"
  echo ""
  
  # 检查 package.json
  if [ ! -f "package.json" ]; then
    echo "❌ package.json 不存在"
    echo "跳过此项目"
    echo ""
    cd "$PROJECT_ROOT"
    continue
  fi
  
  # 检查是否需要安装 Tailwind CSS
  if ! grep -q "tailwindcss" package.json; then
    echo "⚠️  package.json 中未找到 tailwindcss"
    echo "可能需要上传更新后的 package.json"
  fi
  
  # 修复 node_modules 权限（如果存在）
  if [ -d "node_modules" ]; then
    echo "修复 node_modules 权限..."
    chown -R ubuntu:ubuntu node_modules 2>/dev/null || true
    chmod -R u+w node_modules 2>/dev/null || true
  fi
  
  # 安装依赖（使用 ubuntu 用户，不使用 sudo）
  echo "安装依赖..."
  if sudo -u ubuntu npm install 2>&1; then
    echo "✅ 依赖安装成功"
  else
    echo "⚠️  依赖安装失败，尝试使用当前用户..."
    npm install 2>&1 || {
      echo "❌ 依赖安装失败"
      echo "跳过此项目"
      echo ""
      cd "$PROJECT_ROOT"
      continue
    }
  fi
  echo ""
  
  # 构建项目
  echo "构建项目..."
  if sudo -u ubuntu npm run build 2>&1; then
    echo "✅ 构建成功"
  else
    echo "⚠️  构建失败，尝试使用当前用户..."
    npm run build 2>&1 || {
      echo "❌ 构建失败"
      echo "跳过此项目"
      echo ""
      cd "$PROJECT_ROOT"
      continue
    }
  fi
  echo ""
  
  # 返回项目根目录
  cd "$PROJECT_ROOT"
  echo ""
done

# 启动服务
echo "=========================================="
echo "🚀 启动前端服务..."
echo "=========================================="
echo ""

if [ -f "scripts/server/build_and_start_all.sh" ]; then
  echo "执行构建和启动脚本..."
  bash scripts/server/build_and_start_all.sh
else
  echo "⚠️  构建脚本不存在: scripts/server/build_and_start_all.sh"
  echo "请手动启动服务"
fi

echo ""
echo "=========================================="
echo "✅ 完成！"
echo "时间: $(date)"
echo "=========================================="
