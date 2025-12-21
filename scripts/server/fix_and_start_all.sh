#!/bin/bash

# 智能修复并启动所有服务
# 使用方法: bash scripts/server/fix_and_start_all.sh

set -e

echo "=========================================="
echo "🔧 智能修复并启动所有服务"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 清理环境
echo "1. 清理环境..."
echo "----------------------------------------"
echo "停止所有 PM2 进程..."
pm2 delete all 2>/dev/null || true
sleep 2

# 停止可能占用端口的进程
PORTS=(3000 3001 3002 3003 8000)
for PORT in "${PORTS[@]}"; do
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "停止占用端口 $PORT 的进程..."
    sudo lsof -ti :$PORT 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
    sleep 1
  fi
done

echo "✅ 环境清理完成"
echo ""

# 2. 智能定位并启动三个项目
echo "2. 智能定位并启动项目..."
echo "----------------------------------------"

# 定义项目映射：关键词 -> 端口 -> PM2名称
declare -A PROJECTS=(
  ["tgmini"]="3001:tgmini-frontend"
  ["hbwy"]="3002:hongbao-frontend"
  ["hongbao"]="3002:hongbao-frontend"
  ["aizkw"]="3003:aizkw-frontend"
  ["liaotian"]="3003:aizkw-frontend"
)

# 已处理的端口，避免重复启动
declare -A PROCESSED_PORTS=()

for KEYWORD in "${!PROJECTS[@]}"; do
  IFS=':' read -r PORT PM2_NAME <<< "${PROJECTS[$KEYWORD]}"
  
  # 如果该端口已处理，跳过
  if [ -n "${PROCESSED_PORTS[$PORT]}" ]; then
    continue
  fi
  
  echo ""
  echo "查找包含 '$KEYWORD' 的项目..."
  
  # 查找 package.json
  PACKAGE_JSON=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
    grep -iE "(tgmini|hbwy|hongbao|aizkw|liaotian)" | \
    grep -i "$KEYWORD" | head -1)
  
  if [ -z "$PACKAGE_JSON" ]; then
    echo "  ⚠️  未找到包含 '$KEYWORD' 的 package.json"
    continue
  fi
  
  PROJECT_DIR=$(dirname "$PACKAGE_JSON")
  echo "  ✅ 找到项目目录: $PROJECT_DIR"
  
  # 进入项目目录
  cd "$PROJECT_DIR" || {
    echo "  ❌ 无法进入目录: $PROJECT_DIR"
    continue
  }
  
  # 检查 package.json 是否存在
  if [ ! -f "package.json" ]; then
    echo "  ❌ package.json 不存在"
    continue
  fi
  
  # 检查项目名称
  PROJECT_NAME=$(grep -oP '"name"\s*:\s*"[^"]*"' package.json | head -1 | cut -d'"' -f4 || echo "")
  echo "  📦 项目名称: ${PROJECT_NAME:-未知}"
  
  # 2.1 安装依赖
  echo "  📥 安装依赖..."
  if [ ! -d "node_modules" ]; then
    npm install || {
      echo "  ⚠️  依赖安装失败，但继续..."
    }
  else
    echo "  ✅ node_modules 已存在"
  fi
  
  # 2.2 构建项目
  echo "  🔨 构建项目..."
  
  # 检查是否有 build 脚本
  HAS_BUILD=$(grep -q '"build"' package.json && echo "yes" || echo "no")
  
  if [ "$HAS_BUILD" = "yes" ]; then
    # 清理旧构建
    if [ -d "dist" ]; then
      rm -rf dist
    fi
    if [ -d ".next" ]; then
      rm -rf .next
    fi
    
    npm run build || {
      echo "  ⚠️  构建失败，但继续尝试启动..."
    }
  else
    echo "  ⚠️  package.json 中没有 build 脚本，跳过构建"
  fi
  
  # 2.3 确定启动方式
  echo "  🚀 启动服务..."
  
  # 检查构建输出目录
  DIST_DIR=""
  if [ -d "dist" ]; then
    DIST_DIR="dist"
  elif [ -d "build" ]; then
    DIST_DIR="build"
  elif [ -d ".next" ]; then
    DIST_DIR=".next"
  elif [ -d ".next/standalone" ]; then
    DIST_DIR=".next/standalone"
  else
    echo "  ⚠️  未找到构建输出目录，尝试直接启动..."
  fi
  
  # 检查是否有 serve 命令
  if command -v serve >/dev/null 2>&1; then
    SERVE_CMD="serve"
  elif [ -f "node_modules/.bin/serve" ]; then
    SERVE_CMD="node_modules/.bin/serve"
  else
    # 安装 serve
    echo "  📦 安装 serve..."
    npm install -g serve 2>/dev/null || {
      echo "  ⚠️  serve 安装失败，尝试使用 npx..."
      SERVE_CMD="npx serve"
    }
    SERVE_CMD="serve"
  fi
  
  # 启动服务
  if [ -n "$DIST_DIR" ] && [ -d "$DIST_DIR" ]; then
    echo "  ✅ 使用 serve 启动静态文件服务 (目录: $DIST_DIR, 端口: $PORT)"
    pm2 start "$SERVE_CMD" \
      --name "$PM2_NAME" \
      -- -s "$DIST_DIR" -l "$PORT" || {
      echo "  ❌ 启动失败"
      pm2 logs "$PM2_NAME" --lines 10 --nostream 2>/dev/null || true
      continue
    }
  else
    # 尝试使用 npm start
    HAS_START=$(grep -q '"start"' package.json && echo "yes" || echo "no")
    if [ "$HAS_START" = "yes" ]; then
      echo "  ✅ 使用 npm start 启动 (端口: $PORT)"
      # 检查是否需要指定端口
      START_CMD=$(grep '"start"' package.json | head -1 | cut -d'"' -f4)
      if echo "$START_CMD" | grep -q "\-p\|--port"; then
        # 命令中已包含端口
        pm2 start npm \
          --name "$PM2_NAME" \
          --cwd "$PROJECT_DIR" \
          -- start || {
          echo "  ❌ 启动失败"
          continue
        }
      else
        # 需要添加端口参数
        pm2 start npm \
          --name "$PM2_NAME" \
          --cwd "$PROJECT_DIR" \
          -- start -- -p "$PORT" || {
          echo "  ❌ 启动失败"
          continue
        }
      fi
    else
      echo "  ⚠️  无法确定启动方式，跳过..."
      continue
    fi
  fi
  
  echo "  ✅ $PM2_NAME 已启动 (端口 $PORT)"
  PROCESSED_PORTS[$PORT]=1
  
  # 返回项目根目录
  cd "$PROJECT_ROOT" || exit 1
done

echo ""

# 3. 处理 saas-demo (聊天AI后台，端口 3000)
echo "3. 启动 saas-demo (聊天AI后台)..."
echo "----------------------------------------"
SAAS_DEMO_DIR="$PROJECT_ROOT/saas-demo"

if [ -d "$SAAS_DEMO_DIR" ] && [ -f "$SAAS_DEMO_DIR/package.json" ]; then
  echo "找到 saas-demo 目录: $SAAS_DEMO_DIR"
  cd "$SAAS_DEMO_DIR" || exit 1
  
  # 安装依赖
  if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install || {
      echo "⚠️  依赖安装失败，但继续..."
    }
  fi
  
  # 构建
  if [ ! -d ".next" ]; then
    echo "构建 saas-demo..."
    npm run build || {
      echo "⚠️  构建失败，但继续尝试启动..."
    }
  fi
  
  # 启动
  mkdir -p "$SAAS_DEMO_DIR/logs"
  pm2 start npm \
    --name saas-demo \
    --cwd "$SAAS_DEMO_DIR" \
    --error "$SAAS_DEMO_DIR/logs/saas-demo-error.log" \
    --output "$SAAS_DEMO_DIR/logs/saas-demo-out.log" \
    --merge-logs \
    --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
    -- start || {
    echo "⚠️  saas-demo 启动失败"
    pm2 logs saas-demo --lines 10 --nostream 2>/dev/null || true
  }
  
  echo "✅ saas-demo 已启动 (端口 3000)"
else
  echo "⚠️  saas-demo 目录不存在或 package.json 不存在"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 4. 重启后端
echo "4. 重启后端服务..."
echo "----------------------------------------"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"

if [ -d "$BACKEND_DIR" ]; then
  echo "找到后端目录: $BACKEND_DIR"
  
  # 检查是否有 PM2 配置或启动脚本
  if [ -f "$BACKEND_DIR/package.json" ]; then
    cd "$BACKEND_DIR" || exit 1
    
    # 检查是否有 start 脚本
    HAS_START=$(grep -q '"start"' package.json && echo "yes" || echo "no")
    
    if [ "$HAS_START" = "yes" ]; then
      echo "使用 npm start 启动后端..."
      pm2 start npm \
        --name backend \
        --cwd "$BACKEND_DIR" \
        -- start || {
        echo "⚠️  后端启动失败"
        pm2 logs backend --lines 10 --nostream 2>/dev/null || true
      }
    else
      # 尝试查找 Python 启动脚本
      PYTHON_MAIN=$(find "$BACKEND_DIR" -maxdepth 2 -name "main.py" -o -name "app.py" -o -name "run.py" | head -1)
      if [ -n "$PYTHON_MAIN" ]; then
        echo "使用 Python 启动后端: $PYTHON_MAIN"
        pm2 start "$PYTHON_MAIN" \
          --name backend \
          --interpreter python3 || {
          echo "⚠️  后端启动失败"
          pm2 logs backend --lines 10 --nostream 2>/dev/null || true
        }
      else
        echo "⚠️  无法确定后端启动方式"
      fi
    fi
    
    echo "✅ 后端已启动 (端口 8000)"
  else
    echo "⚠️  后端目录中未找到 package.json"
  fi
else
  echo "⚠️  后端目录不存在: $BACKEND_DIR"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 5. 等待服务启动
echo "5. 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 6. 最终检查
echo "6. 最终检查..."
echo "----------------------------------------"

# 保存 PM2 配置
pm2 save || true
echo "✅ PM2 配置已保存"
echo ""

# 显示 PM2 进程列表
echo "PM2 进程列表："
pm2 list
echo ""

# 显示监听端口
echo "当前监听端口："
if command -v netstat >/dev/null 2>&1; then
  netstat -ntlp | grep LISTEN || echo "无法获取端口信息"
elif command -v ss >/dev/null 2>&1; then
  ss -tlnp | grep LISTEN || echo "无法获取端口信息"
else
  echo "⚠️  netstat 和 ss 都不可用"
fi
echo ""

# 检查关键端口
echo "检查关键端口状态："
PORTS=(3000 3001 3002 3003 8000)
ALL_OK=true

for PORT in "${PORTS[@]}"; do
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "✅ 端口 $PORT 正在监听"
    
    # 测试 HTTP 响应
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
echo "=========================================="
if [ "$ALL_OK" = "true" ]; then
  echo "✅ 所有服务启动成功！"
else
  echo "⚠️  部分服务可能未正常启动，请检查上述输出"
fi
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查："
echo "1. PM2 日志: pm2 logs"
echo "2. 端口占用: sudo lsof -i :PORT"
echo "3. Nginx 配置: sudo nginx -t"
echo "4. 防火墙: sudo ufw status"
