#!/bin/bash

# 终极修复脚本：强制启动 4 个网站到正确端口
# 使用方法: bash scripts/server/force_start_4_sites.sh

set -e

echo "=========================================="
echo "🔧 终极修复：强制启动 4 个网站到正确端口"
echo "时间: $(date)"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || {
  echo "❌ 无法进入项目目录: $PROJECT_ROOT"
  exit 1
}

# 1. 清场：停止所有进程
echo "1. 清场：停止所有进程..."
echo "----------------------------------------"

# 停止所有 PM2 进程
pm2 delete all 2>/dev/null || true
sleep 2

# 停止所有占用端口的进程
PORTS=(3000 3001 3002 3003 8000)
for PORT in "${PORTS[@]}"; do
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "停止占用端口 $PORT 的进程..."
    PIDS=$(lsof -ti :$PORT 2>/dev/null || ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP "pid=\K\d+" || echo "")
    for PID in $PIDS; do
      if [ -n "$PID" ] && [ "$PID" != "N/A" ]; then
        sudo kill -9 $PID 2>/dev/null || true
      fi
    done
    sleep 1
  fi
done

echo "✅ 清场完成"
echo ""

# 2. 定义启动前端服务的函数
start_frontend() {
  local KEYWORD=$1
  local PM2_NAME=$2
  local PORT=$3
  
  echo "启动 $PM2_NAME (端口 $PORT)..."
  echo "----------------------------------------"
  
  # 查找项目目录
  local PROJECT_DIR=""
  
  # 根据关键词查找目录
  if [ "$KEYWORD" = "saas-demo" ]; then
    # saas-demo 固定路径
    if [ -d "$PROJECT_ROOT/saas-demo" ] && [ -f "$PROJECT_ROOT/saas-demo/package.json" ]; then
      PROJECT_DIR="$PROJECT_ROOT/saas-demo"
    fi
  elif [ "$KEYWORD" = "tgmini" ]; then
    # 查找包含 tgmini 的目录
    PROJECT_DIR=$(find "$PROJECT_ROOT" -maxdepth 3 -type d -name "*tgmini*" 2>/dev/null | \
      grep -v "/\.git/" | head -1 || echo "")
  elif [ "$KEYWORD" = "hongbao" ] || [ "$KEYWORD" = "hbwy" ]; then
    # 优先查找 react-vite-template/hbwy20251220
    if [ -d "$PROJECT_ROOT/react-vite-template/hbwy20251220" ] && [ -f "$PROJECT_ROOT/react-vite-template/hbwy20251220/package.json" ]; then
      PROJECT_DIR="$PROJECT_ROOT/react-vite-template/hbwy20251220"
    else
      # 查找包含 hbwy 或 hongbao 的目录
      PROJECT_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
        grep -iE "(hbwy|hongbao)" | \
        grep -v "/\.git/" | \
        head -1 | xargs dirname 2>/dev/null || echo "")
    fi
  elif [ "$KEYWORD" = "aizkw" ]; then
    # 优先查找标准路径
    if [ -d "$PROJECT_ROOT/aizkw20251219" ] && [ -f "$PROJECT_ROOT/aizkw20251219/package.json" ]; then
      PROJECT_DIR="$PROJECT_ROOT/aizkw20251219"
    elif [ -d "$PROJECT_ROOT/migrations/aizkw20251219" ] && [ -f "$PROJECT_ROOT/migrations/aizkw20251219/package.json" ]; then
      PROJECT_DIR="$PROJECT_ROOT/migrations/aizkw20251219"
    else
      # 查找包含 aizkw 的目录，排除 logs
      PROJECT_DIR=$(find "$PROJECT_ROOT" -maxdepth 5 -type f -name "package.json" 2>/dev/null | \
        grep -iE "aizkw" | \
        grep -v "/logs/" | \
        grep -v "/\.git/" | \
        head -1 | xargs dirname 2>/dev/null || echo "")
    fi
  fi
  
  if [ -z "$PROJECT_DIR" ] || [ ! -f "$PROJECT_DIR/package.json" ]; then
    echo "❌ 未找到 $KEYWORD 项目目录"
    return 1
  fi
  
  echo "找到项目目录: $PROJECT_DIR"
  cd "$PROJECT_DIR" || return 1
  
  # 安装依赖
  if [ ! -d "node_modules" ]; then
    echo "安装依赖..."
    npm install || {
      echo "⚠️  依赖安装失败，但继续..."
    }
  else
    echo "✅ node_modules 已存在"
  fi
  
  # 构建项目
  echo "构建项目..."
  rm -rf dist build .next
  npm run build || {
    echo "❌ 构建失败"
    cd "$PROJECT_ROOT" || exit 1
    return 1
  }
  
  # 确定构建输出目录
  local BUILD_DIR=""
  if [ -d "dist" ]; then
    BUILD_DIR="dist"
  elif [ -d "build" ]; then
    BUILD_DIR="build"
  elif [ -d ".next" ]; then
    BUILD_DIR=".next"
  fi
  
  if [ -z "$BUILD_DIR" ]; then
    echo "❌ 未找到构建输出目录"
    cd "$PROJECT_ROOT" || exit 1
    return 1
  fi
  
  echo "✅ 构建完成，输出目录: $BUILD_DIR"
  
  # 启动服务
  if [ "$KEYWORD" = "saas-demo" ]; then
    # saas-demo 使用 npm start
    mkdir -p "$PROJECT_DIR/logs"
    pm2 start npm \
      --name "$PM2_NAME" \
      --cwd "$PROJECT_DIR" \
      --error "$PROJECT_DIR/logs/${PM2_NAME}-error.log" \
      --output "$PROJECT_DIR/logs/${PM2_NAME}-out.log" \
      --merge-logs \
      --log-date-format "YYYY-MM-DD HH:mm:ss Z" \
      -- start || {
      echo "❌ $PM2_NAME 启动失败"
      cd "$PROJECT_ROOT" || exit 1
      return 1
    }
  elif [ "$BUILD_DIR" = "dist" ] || [ "$BUILD_DIR" = "build" ]; then
    # 使用 serve 启动静态文件
    pm2 start serve \
      --name "$PM2_NAME" \
      -- -s "$BUILD_DIR" -l "$PORT" || {
      echo "❌ $PM2_NAME 启动失败"
      cd "$PROJECT_ROOT" || exit 1
      return 1
    }
  else
    echo "❌ 无法确定启动方式"
    cd "$PROJECT_ROOT" || exit 1
    return 1
  fi
  
  echo "✅ $PM2_NAME 已启动 (端口 $PORT)"
  cd "$PROJECT_ROOT" || exit 1
  return 0
}

# 3. 按顺序启动前端服务
echo "2. 启动前端服务..."
echo "=========================================="
echo ""

# 3.1 启动 saas-demo (端口 3000)
start_frontend "saas-demo" "saas-demo" "3000"
echo ""

# 3.2 启动 tgmini-frontend (端口 3001)
start_frontend "tgmini" "tgmini-frontend" "3001"
echo ""

# 3.3 启动 hongbao-frontend (端口 3002)
start_frontend "hongbao" "hongbao-frontend" "3002"
echo ""

# 3.4 启动 aizkw-frontend (端口 3003)
start_frontend "aizkw" "aizkw-frontend" "3003"
echo ""

# 4. 启动后端服务
echo "3. 启动后端服务..."
echo "----------------------------------------"
BACKEND_DIR="$PROJECT_ROOT/admin-backend"

if [ -d "$BACKEND_DIR" ]; then
  echo "找到后端目录: $BACKEND_DIR"
  cd "$BACKEND_DIR" || exit 1
  
  # 检查是否有 package.json (Node.js 后端)
  if [ -f "package.json" ]; then
    if [ ! -d "node_modules" ]; then
      npm install || echo "⚠️  依赖安装失败，但继续..."
    fi
    
    HAS_START=$(grep -q '"start"' package.json && echo "yes" || echo "no")
    if [ "$HAS_START" = "yes" ]; then
      pm2 start npm \
        --name backend \
        --cwd "$BACKEND_DIR" \
        -- start || {
        echo "⚠️  后端启动失败"
      }
      echo "✅ 后端已启动 (端口 8000)"
    fi
  else
    # 查找 Python 启动文件
    PYTHON_MAIN=$(find "$BACKEND_DIR" -maxdepth 2 -name "main.py" -o -name "app.py" -o -name "run.py" | head -1)
    if [ -n "$PYTHON_MAIN" ]; then
      echo "使用 Python 启动后端: $PYTHON_MAIN"
      pm2 start "$PYTHON_MAIN" \
        --name backend \
        --interpreter python3 || {
        echo "⚠️  后端启动失败"
      }
      echo "✅ 后端已启动 (端口 8000)"
    else
      echo "⚠️  无法确定后端启动方式"
    fi
  fi
else
  echo "⚠️  后端目录不存在: $BACKEND_DIR"
fi

cd "$PROJECT_ROOT" || exit 1
echo ""

# 5. 等待服务启动
echo "4. 等待服务启动..."
echo "----------------------------------------"
sleep 10

# 6. 保存 PM2 配置
echo "5. 保存 PM2 配置..."
echo "----------------------------------------"
pm2 save || true
echo "✅ PM2 配置已保存"
echo ""

# 7. 重启 Nginx
echo "6. 重启 Nginx..."
echo "----------------------------------------"
sudo systemctl restart nginx || {
  echo "⚠️  Nginx 重启失败"
}
sleep 2

if systemctl is-active --quiet nginx; then
  echo "✅ Nginx 已重启"
else
  echo "⚠️  Nginx 未运行"
fi
echo ""

# 8. 验证所有端口
echo "7. 验证所有端口..."
echo "----------------------------------------"
ALL_OK=true

for PORT in 3000 3001 3002 3003 8000; do
  if lsof -i :$PORT >/dev/null 2>&1 || ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "✅ 端口 $PORT 正在监听"
    
    # 测试 HTTP 响应（仅对前端端口）
    if [ "$PORT" != "8000" ]; then
      HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$PORT 2>/dev/null || echo "000")
      if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
        echo "   ✅ HTTP 响应正常 (HTTP $HTTP_CODE)"
      else
        echo "   ⚠️  HTTP 响应异常 (HTTP $HTTP_CODE)"
        ALL_OK=false
      fi
    fi
  else
    echo "❌ 端口 $PORT 未监听"
    ALL_OK=false
  fi
done

echo ""

# 9. 显示 PM2 进程列表
echo "8. PM2 进程列表："
echo "----------------------------------------"
pm2 list

echo ""

# 10. 显示监听端口
echo "9. 当前监听端口："
echo "----------------------------------------"
if command -v netstat >/dev/null 2>&1; then
  netstat -ntlp | grep LISTEN || echo "无法获取端口信息"
elif command -v ss >/dev/null 2>&1; then
  ss -tlnp | grep LISTEN || echo "无法获取端口信息"
else
  echo "⚠️  netstat 和 ss 都不可用"
fi

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
echo "端口映射："
echo "  3000 -> saas-demo (聊天AI后台)"
echo "  3001 -> tgmini-frontend"
echo "  3002 -> hongbao-frontend"
echo "  3003 -> aizkw-frontend"
echo "  8000 -> backend"
echo ""
echo "如果仍有问题，请检查："
echo "  pm2 logs"
echo "  sudo systemctl status nginx"
