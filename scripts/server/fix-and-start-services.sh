#!/bin/bash
# 修复并启动服务脚本

set -e  # 遇到错误立即退出

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "========================================="
echo "修复并启动服务"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 错误处理函数
error_exit() {
    echo -e "${RED}❌ 错误: $1${NC}"
    exit 1
}

# 成功消息
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 信息消息
info_msg() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# 步骤 1: 检查并安装 npm
echo "[1/6] 检查 npm..."
if ! command -v npm &> /dev/null; then
    info_msg "npm 未安装，正在安装..."
    # 确保 Node.js 20 已安装，npm 应该包含在内
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs || error_exit "npm 安装失败"
fi

NPM_VERSION=$(npm --version)
NODE_VERSION=$(node --version)
success_msg "npm 版本: $NPM_VERSION, Node.js 版本: $NODE_VERSION"
echo ""

# 步骤 2: 完成前端配置和构建
echo "[2/6] 配置前端..."
cd "$FRONTEND_DIR" || error_exit "无法进入前端目录"

# 检查是否已经构建
if [ ! -f ".next/standalone/server.js" ]; then
    info_msg "前端尚未构建，开始构建..."
    info_msg "安装前端依赖（这可能需要几分钟）..."
    npm install --prefer-offline --no-audit --no-fund || error_exit "安装前端依赖失败"
    
    info_msg "构建前端（这可能需要5-10分钟）..."
    export NODE_OPTIONS="--max-old-space-size=4096"
    npm run build || error_exit "前端构建失败"
    
    # 处理静态资源
    info_msg "处理静态资源..."
    mkdir -p .next/standalone/.next/static || true
    cp -r .next/static/* .next/standalone/.next/static/ 2>/dev/null || true
    cp -r public .next/standalone/ 2>/dev/null || true
    success_msg "前端构建完成"
else
    success_msg "前端已构建，跳过构建步骤"
fi
echo ""

# 步骤 3: 检查后端配置
echo "[3/6] 检查后端配置..."
cd "$BACKEND_DIR" || error_exit "无法进入后端目录"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    info_msg "创建 Python 虚拟环境..."
    python3 -m venv venv || error_exit "创建虚拟环境失败"
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet || error_exit "安装后端依赖失败"
    success_msg "后端依赖安装完成"
else
    success_msg "后端虚拟环境已存在"
fi
echo ""

# 步骤 4: 检查服务配置文件
echo "[4/6] 检查服务配置..."
cd "$PROJECT_DIR"

# 确保服务文件存在
if [ ! -f "/etc/systemd/system/luckyred-api.service" ]; then
    info_msg "后端服务文件不存在，正在创建..."
    if [ -f "$PROJECT_DIR/deploy/systemd/luckyred-api.service" ]; then
        sudo cp "$PROJECT_DIR/deploy/systemd/luckyred-api.service" /etc/systemd/system/
    else
        sudo tee /etc/systemd/system/luckyred-api.service > /dev/null <<EOF
[Unit]
Description=LuckyRed API Service (FastAPI)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH=$BACKEND_DIR"
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=luckyred-api
NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
    fi
fi

if [ ! -f "/etc/systemd/system/liaotian-frontend.service" ]; then
    info_msg "前端服务文件不存在，正在创建..."
    if [ -f "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" ]; then
        sudo cp "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" /etc/systemd/system/
    else
        sudo tee /etc/systemd/system/liaotian-frontend.service > /dev/null <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$FRONTEND_DIR
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
ExecStart=/usr/bin/node .next/standalone/server.js
Restart=always
RestartSec=5
LimitNOFILE=65535
StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOF
    fi
fi

# 重新加载 systemd
sudo systemctl daemon-reload
success_msg "服务配置已更新"
echo ""

# 步骤 5: 修复文件权限
echo "[5/6] 修复文件权限..."
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR"
success_msg "文件权限已修复"
echo ""

# 步骤 6: 启动服务并诊断
echo "[6/6] 启动服务..."

# 启用服务
sudo systemctl enable luckyred-api
sudo systemctl enable liaotian-frontend

# 停止可能存在的旧服务
sudo systemctl stop luckyred-api 2>/dev/null || true
sudo systemctl stop liaotian-frontend 2>/dev/null || true
sleep 2

# 启动后端服务
info_msg "启动后端服务..."
sudo systemctl start luckyred-api
sleep 5

# 检查后端服务状态
if sudo systemctl is-active --quiet luckyred-api; then
    success_msg "后端服务已启动"
else
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    echo "查看错误日志:"
    sudo journalctl -u luckyred-api -n 30 --no-pager
    error_exit "后端服务启动失败，请查看上面的日志"
fi

# 启动前端服务
info_msg "启动前端服务..."
sudo systemctl start liaotian-frontend
sleep 5

# 检查前端服务状态
if sudo systemctl is-active --quiet liaotian-frontend; then
    success_msg "前端服务已启动"
else
    echo -e "${RED}❌ 前端服务启动失败${NC}"
    echo "查看错误日志:"
    sudo journalctl -u liaotian-frontend -n 30 --no-pager
    info_msg "前端服务启动失败，请查看上面的日志"
fi

# 确保 Nginx 运行
sudo systemctl start nginx 2>/dev/null || true
sleep 2

echo ""
echo "========================================="
echo "服务状态验证"
echo "========================================="
echo ""

# 检查服务状态
check_service() {
    local service=$1
    if sudo systemctl is-active --quiet "$service"; then
        success_msg "$service 正在运行"
        return 0
    else
        echo -e "${RED}❌ $service 未运行${NC}"
        return 1
    fi
}

check_service "luckyred-api"
check_service "liaotian-frontend"
check_service "nginx"
echo ""

# 检查端口监听
echo "端口监听状态:"
PORT_8000=$(sudo ss -tlnp | grep :8000 | wc -l)
PORT_3000=$(sudo ss -tlnp | grep :3000 | wc -l)
PORT_443=$(sudo ss -tlnp | grep :443 | wc -l)

if [ "$PORT_8000" -gt 0 ]; then
    success_msg "端口 8000 (后端) 正在监听"
else
    echo -e "${RED}❌ 端口 8000 未监听${NC}"
fi

if [ "$PORT_3000" -gt 0 ]; then
    success_msg "端口 3000 (前端) 正在监听"
else
    echo -e "${RED}❌ 端口 3000 未监听${NC}"
fi

if [ "$PORT_443" -gt 0 ]; then
    success_msg "端口 443 (HTTPS) 正在监听"
else
    info_msg "端口 443 (HTTPS) 未监听（如需 HTTPS 请配置 SSL 证书）"
fi
echo ""

# 健康检查
echo "执行健康检查..."
sleep 3

BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    success_msg "后端健康检查通过 (HTTP $BACKEND_HEALTH)"
else
    echo -e "${RED}❌ 后端健康检查失败 (HTTP $BACKEND_HEALTH)${NC}"
fi

FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "304" ]; then
    success_msg "前端服务响应正常 (HTTP $FRONTEND_HEALTH)"
else
    echo -e "${RED}❌ 前端服务响应异常 (HTTP $FRONTEND_HEALTH)${NC}"
fi

echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "如果服务未正常运行，请查看日志:"
echo "  后端: sudo journalctl -u luckyred-api -n 50 --no-pager"
echo "  前端: sudo journalctl -u liaotian-frontend -n 50 --no-pager"
echo ""
echo "访问地址:"
echo "  HTTP: http://aikz.usdt2026.cc"
echo ""
