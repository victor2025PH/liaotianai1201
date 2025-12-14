#!/bin/bash
# ============================================================
# 修复前端服务 502 错误（端口 3000 未运行）
# ============================================================

set +e  # 不在第一个错误时退出

echo "=========================================="
echo "🔧 修复前端服务 502 错误"
echo "=========================================="
echo ""

# Step 1: 检查端口 3000
echo "[1/5] 检查端口 3000..."
PORT_3000_PID=$(sudo ss -tlnp 2>/dev/null | grep ":3000" | awk '{print $6}' | grep -oP 'pid=\K\d+' | head -n 1 || echo "")
if [ -n "$PORT_3000_PID" ]; then
  echo "  ✅ 端口 3000 正在监听 (PID: $PORT_3000_PID)"
  echo "  进程信息:"
  ps -fp "$PORT_3000_PID" 2>/dev/null | tail -1 || echo "  无法获取进程信息"
else
  echo "  ❌ 端口 3000 未监听（前端服务未运行）"
fi

# Step 2: 检查前端服务
echo ""
echo "[2/5] 检查前端服务..."
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

if [ ! -d "$FRONTEND_DIR" ]; then
  # 尝试其他可能的位置
  if [ -d "/home/ubuntu/telegram-ai-system/saas-demo" ]; then
    FRONTEND_DIR="/home/ubuntu/telegram-ai-system/saas-demo"
  elif [ -d "$(pwd)/saas-demo" ]; then
    FRONTEND_DIR="$(pwd)/saas-demo"
  else
    echo "  ❌ 前端目录不存在"
    echo "  请检查前端项目位置"
    exit 1
  fi
fi

echo "  前端目录: $FRONTEND_DIR"

# Step 3: 检查 Nginx 配置
echo ""
echo "[3/5] 检查 Nginx 配置..."
NGINX_CONFIG="/etc/nginx/sites-available/default"
if grep -q "proxy_pass.*127.0.0.1:3000" "$NGINX_CONFIG"; then
  echo "  ⚠️  Nginx 配置中 `/` 路径代理到端口 3000"
  echo "  但前端服务未运行，导致 502 错误"
  
  # 显示相关配置
  echo ""
  echo "  相关配置:"
  grep -B 5 -A 10 "proxy_pass.*127.0.0.1:3000" "$NGINX_CONFIG" | head -20
else
  echo "  ✅ Nginx 配置中未找到端口 3000 的代理"
fi

# Step 4: 选择修复方案
echo ""
echo "[4/5] 选择修复方案..."
echo ""
echo "  方案 1: 启动前端服务（推荐，如果前端需要运行）"
echo "  方案 2: 修改 Nginx 配置，将前端路径也代理到后端（如果前端是静态文件）"
echo ""
read -p "  请选择方案 (1/2，默认 1): " choice
choice=${choice:-1}

if [ "$choice" = "1" ]; then
  # 方案 1: 启动前端服务
  echo ""
  echo "  启动前端服务..."
  
  cd "$FRONTEND_DIR" || exit 1
  
  # 检查 node_modules
  if [ ! -d "node_modules" ]; then
    echo "  安装依赖..."
    npm install || {
      echo "  ❌ 依赖安装失败"
      exit 1
    }
  fi
  
  # 检查是否已有进程在运行
  if [ -n "$PORT_3000_PID" ]; then
    echo "  端口 3000 已被占用，先停止现有进程..."
    sudo kill -9 "$PORT_3000_PID" 2>/dev/null || true
    sleep 2
  fi
  
  # 启动前端服务（后台运行）
  echo "  启动 Next.js 开发服务器..."
  nohup npm run dev > /tmp/frontend.log 2>&1 &
  FRONTEND_PID=$!
  
  echo "  前端服务已启动 (PID: $FRONTEND_PID)"
  echo "  日志文件: /tmp/frontend.log"
  
  # 等待服务启动
  echo "  等待服务启动..."
  sleep 10
  
  # 检查服务是否启动成功
  if curl -s --max-time 5 http://localhost:3000 >/dev/null 2>&1; then
    echo "  ✅ 前端服务启动成功"
  else
    echo "  ⚠️  前端服务可能还在启动中，请检查日志: tail -f /tmp/frontend.log"
  fi
  
elif [ "$choice" = "2" ]; then
  # 方案 2: 修改 Nginx 配置
  echo ""
  echo "  修改 Nginx 配置..."
  
  # 备份配置
  sudo cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
  echo "  配置已备份"
  
  # 修改配置：将端口 3000 改为 8000（或使用静态文件）
  echo ""
  echo "  请手动编辑 Nginx 配置:"
  echo "  sudo nano $NGINX_CONFIG"
  echo ""
  echo "  将以下内容:"
  echo "    proxy_pass http://127.0.0.1:3000;"
  echo "  改为:"
  echo "    proxy_pass http://127.0.0.1:8000;"
  echo "  或者配置静态文件服务"
  echo ""
  read -p "  按 Enter 继续..."
  
  # 测试配置
  if sudo nginx -t; then
    echo "  ✅ Nginx 配置语法正确"
    echo "  重新加载 Nginx..."
    sudo systemctl reload nginx
  else
    echo "  ❌ Nginx 配置有错误，请检查"
    exit 1
  fi
fi

# Step 5: 验证修复
echo ""
echo "[5/5] 验证修复..."
sleep 3

# 检查端口 3000
if sudo ss -tlnp 2>/dev/null | grep -q ":3000"; then
  echo "  ✅ 端口 3000 正在监听"
else
  echo "  ⚠️  端口 3000 未监听（如果选择了方案 2，这是正常的）"
fi

# 测试访问
echo "  测试访问..."
if curl -s --max-time 5 http://localhost:3000 >/dev/null 2>&1; then
  echo "  ✅ http://localhost:3000 可访问"
elif curl -s --max-time 5 http://localhost:8000 >/dev/null 2>&1; then
  echo "  ✅ http://localhost:8000 可访问（后端服务正常）"
else
  echo "  ⚠️  本地服务测试失败"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "如果仍有 502 错误，请检查："
echo "  1. 前端服务日志: tail -f /tmp/frontend.log"
echo "  2. Nginx 错误日志: sudo tail -50 /var/log/nginx/error.log"
echo "  3. 前端服务状态: ps aux | grep node"
echo ""
