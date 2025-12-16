#!/bin/bash
# ============================================================
# Fix CPU Loop - Stop Service and Rebuild (Server Environment - Linux)
# ============================================================
#
# Running Environment: Server Linux Environment
# Function: Stop frontend service stuck in restart loop, fix TypeScript error, rebuild, and restart
#
# One-click execution: sudo bash scripts/server/fix_cpu_loop.sh
# ============================================================

set -e

echo "============================================================"
echo "🔧 修复 CPU 死循环 - 停止服务并重新构建"
echo "============================================================"
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
SERVICE_NAME="liaotian-frontend"
TS_FILE="$FRONTEND_DIR/src/app/group-ai/groups/page.tsx"

# 步骤 1: 立刻止血（停止服务）
echo "[1/4] 立刻止血 - 停止前端服务"
echo "----------------------------------------"
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
  echo "停止 $SERVICE_NAME 服务..."
  sudo systemctl stop "$SERVICE_NAME" && echo "✅ $SERVICE_NAME 已停止" || echo "⚠️  停止失败（可能已经停止）"
else
  echo "✅ $SERVICE_NAME 服务未运行"
fi

# 等待服务完全停止
sleep 2

# 检查 CPU 使用情况
echo ""
echo "当前 CPU 使用情况（Top 5 进程）:"
top -b -n 1 | head -n 12 | tail -n 7 || echo "无法获取 CPU 信息"

echo ""

# 步骤 2: 修复代码 Bug
echo "[2/4] 修复 TypeScript 错误"
echo "----------------------------------------"
if [ ! -f "$TS_FILE" ]; then
  echo "❌ 文件不存在: $TS_FILE"
  exit 1
fi

echo "检查文件: $TS_FILE"

# 检查是否包含有问题的代码
if grep -q "group\.username\.replace" "$TS_FILE"; then
  echo "找到需要修复的代码行..."
  
  # 备份原文件
  sudo cp "$TS_FILE" "${TS_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
  echo "✅ 已备份原文件"
  
  # 修复代码：将 group.username.replace('@', '') 改为 (group.username || '').replace('@', '')
  # 使用 sed 进行替换，处理多种可能的写法
  sudo sed -i 's/group\.username\.replace(\([^)]*\))/(group.username || "").replace(\1)/g' "$TS_FILE" || {
    echo "⚠️  sed 替换失败，尝试手动修复..."
    # 如果 sed 失败，使用更精确的替换
    sudo sed -i "s/group\.username\.replace('@', '')/(group.username || '').replace('@', '')/g" "$TS_FILE" || {
      echo "❌ 自动修复失败，请手动修复文件"
      exit 1
    }
  }
  
  echo "✅ TypeScript 错误已修复"
  
  # 显示修复后的代码行
  echo ""
  echo "修复后的相关代码行:"
  grep -n "username.*replace" "$TS_FILE" | head -5 || echo "未找到相关代码"
else
  echo "✅ 未发现需要修复的代码（可能已经修复）"
fi

echo ""

# 步骤 3: 重新构建
echo "[3/4] 重新构建前端"
echo "----------------------------------------"
cd "$FRONTEND_DIR" || {
  echo "❌ 无法进入前端目录: $FRONTEND_DIR"
  exit 1
}

echo "清理旧的构建缓存..."
rm -rf .next
echo "✅ 已清理 .next 目录"

echo ""
echo "开始构建（这可能需要几分钟）..."
export NODE_ENV=production
export NODE_OPTIONS="--max-old-space-size=4096"

# 执行构建并捕获输出
BUILD_LOG="/tmp/frontend_build_$(date +%Y%m%d_%H%M%S).log"
npm run build 2>&1 | tee "$BUILD_LOG"

# 检查构建是否成功
if grep -q "Compiled successfully" "$BUILD_LOG"; then
  echo ""
  echo "✅ 构建成功！"
  
  # 验证关键文件是否存在
  if [ -f ".next/standalone/saas-demo/server.js" ]; then
    echo "✅ server.js 文件已生成: .next/standalone/saas-demo/server.js"
    ls -lh ".next/standalone/saas-demo/server.js"
  else
    echo "⚠️  server.js 文件未找到，但构建显示成功"
    echo "查找 server.js 文件..."
    find .next -name "server.js" -type f 2>/dev/null | head -5 || echo "未找到 server.js"
  fi
else
  echo ""
  echo "❌ 构建失败！未找到 'Compiled successfully' 消息"
  echo "构建日志（最后 50 行）:"
  tail -50 "$BUILD_LOG" || echo "无法读取构建日志"
  exit 1
fi

echo ""

# 步骤 4: 恢复服务
echo "[4/4] 恢复服务"
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

# 检查服务配置
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
if [ -f "$SERVICE_FILE" ]; then
  echo "检查服务配置..."
  CURRENT_PATH=$(grep "ExecStart=" "$SERVICE_FILE" 2>/dev/null | grep -o "\.next/standalone[^ ]*" || echo "")
  EXPECTED_PATH=".next/standalone/saas-demo/server.js"
  
  if [ "$CURRENT_PATH" != "$EXPECTED_PATH" ]; then
    echo "⚠️  服务路径不匹配，修复服务配置..."
    if [ -f "scripts/server/fix-frontend-service-path.sh" ]; then
      bash scripts/server/fix-frontend-service-path.sh || {
        echo "⚠️  服务配置修复失败，但继续启动服务..."
      }
    fi
  fi
fi

echo "启动 $SERVICE_NAME 服务..."
sudo systemctl start "$SERVICE_NAME" && echo "✅ $SERVICE_NAME 已启动" || {
  echo "❌ 启动失败"
  echo "查看服务状态:"
  sudo systemctl status "$SERVICE_NAME" --no-pager | head -20
  exit 1
}

# 等待服务启动
sleep 5

# 检查服务状态
echo ""
echo "=== 服务状态 ==="
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
  echo "✅ $SERVICE_NAME 服务运行正常"
  sudo systemctl status "$SERVICE_NAME" --no-pager | head -10
else
  echo "❌ $SERVICE_NAME 服务未运行"
  echo "查看服务日志:"
  sudo journalctl -u "$SERVICE_NAME" -n 30 --no-pager | tail -20
  exit 1
fi

# 检查端口监听
echo ""
echo "=== 端口监听 ==="
if ss -tlnp | grep -q ":3000"; then
  echo "✅ 端口 3000 正在监听"
  ss -tlnp | grep ":3000"
else
  echo "⚠️  端口 3000 未监听"
fi

# 检查 CPU 使用情况
echo ""
echo "=== CPU 使用情况（修复后）==="
top -b -n 1 | head -n 12 | tail -n 7 || echo "无法获取 CPU 信息"

echo ""
echo "============================================================"
echo "✅ 修复完成"
echo "============================================================"
echo ""
echo "如果服务仍然有问题，请检查："
echo "  1. 服务日志: sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
echo "  2. 构建日志: cat $BUILD_LOG"
echo "  3. 服务配置: sudo systemctl cat $SERVICE_NAME"

