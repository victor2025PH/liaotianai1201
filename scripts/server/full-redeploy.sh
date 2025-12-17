#!/bin/bash
# 完整重新部署脚本
# 适用于服务器重新部署或修复

set -e  # 遇到错误立即退出

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "========================================="
echo "完整重新部署脚本"
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

# 步骤 1: 检查基本环境
echo "[1/10] 检查基本环境..."

# 检查 Git
if ! command -v git &> /dev/null; then
    info_msg "Git 未安装，正在安装..."
    sudo apt-get update -qq
    sudo apt-get install -y git || error_exit "Git 安装失败"
fi

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    info_msg "项目目录不存在，正在从 GitHub 克隆..."
    sudo mkdir -p "$(dirname "$PROJECT_DIR")"
    sudo chown -R ubuntu:ubuntu "$(dirname "$PROJECT_DIR")"
    cd "$(dirname "$PROJECT_DIR")"
    git clone https://github.com/victor2025PH/liaotianai1201.git "$(basename "$PROJECT_DIR")" || error_exit "Git clone 失败"
    cd "$PROJECT_DIR"
else
    cd "$PROJECT_DIR"
    info_msg "拉取最新代码..."
    # 检查是否是 git 仓库
    if [ ! -d ".git" ]; then
        info_msg "当前目录不是 git 仓库，正在初始化..."
        git init || error_exit "Git init 失败"
        git remote add origin https://github.com/victor2025PH/liaotianai1201.git 2>/dev/null || true
        git fetch origin || error_exit "Git fetch 失败"
        git reset --hard origin/main || error_exit "Git reset 失败"
    else
        git fetch origin main || error_exit "Git fetch 失败"
        git reset --hard origin/main || error_exit "Git reset 失败"
    fi
fi
success_msg "代码更新完成"
echo ""

# 步骤 2: 停止现有服务
echo "[2/10] 停止现有服务..."
sudo systemctl stop luckyred-api 2>/dev/null || true
sudo systemctl stop liaotian-frontend 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true
sleep 2
success_msg "服务已停止"
echo ""

# 步骤 3: 配置后端
echo "[3/10] 配置后端..."
cd "$BACKEND_DIR"

# 检查 Python venv
if [ ! -d "venv" ]; then
    info_msg "创建 Python 虚拟环境..."
    python3 -m venv venv || error_exit "创建虚拟环境失败"
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
info_msg "安装后端依赖..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet || error_exit "安装后端依赖失败"
success_msg "后端依赖安装完成"
echo ""

# 步骤 4: 配置前端
echo "[4/10] 配置前端..."
cd "$FRONTEND_DIR"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    error_exit "Node.js 未安装，请先安装 Node.js"
fi

info_msg "安装前端依赖..."
npm install --prefer-offline --no-audit --no-fund || error_exit "安装前端依赖失败"

# 构建前端
info_msg "构建前端（这可能需要几分钟）..."
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build || error_exit "前端构建失败"

# 复制静态资源（Next.js standalone 模式需要）
info_msg "处理静态资源..."
mkdir -p .next/standalone/.next/static || true
cp -r .next/static/* .next/standalone/.next/static/ 2>/dev/null || true
cp -r public .next/standalone/ 2>/dev/null || true

success_msg "前端构建完成"
echo ""

# 步骤 5: 配置 systemd 服务
echo "[5/10] 配置 systemd 服务..."

# 复制服务文件
if [ -f "$PROJECT_DIR/deploy/systemd/luckyred-api.service" ]; then
    sudo cp "$PROJECT_DIR/deploy/systemd/luckyred-api.service" /etc/systemd/system/
    success_msg "后端服务文件已复制"
else
    info_msg "后端服务文件不存在，使用默认配置..."
    sudo tee /etc/systemd/system/luckyred-api.service > /dev/null <<EOF
[Unit]
Description=Luckyred Backend API Service
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/bin:/bin"
ExecStart=$BACKEND_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=luckyred-api

[Install]
WantedBy=multi-user.target
EOF
    success_msg "后端服务文件已创建"
fi

if [ -f "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" ]; then
    sudo cp "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" /etc/systemd/system/
    success_msg "前端服务文件已复制"
else
    info_msg "前端服务文件不存在，使用默认配置..."
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
    success_msg "前端服务文件已创建"
fi

# 重新加载 systemd
sudo systemctl daemon-reload
success_msg "systemd 配置已更新"
echo ""

# 步骤 6: 配置 Nginx
echo "[6/10] 配置 Nginx..."

# 检查是否有 Nginx 配置脚本
if [ -f "$PROJECT_DIR/scripts/server/create-nginx-config.sh" ]; then
    info_msg "使用 Nginx 配置脚本..."
    chmod +x "$PROJECT_DIR/scripts/server/create-nginx-config.sh"
    sudo bash "$PROJECT_DIR/scripts/server/create-nginx-config.sh" || info_msg "Nginx 配置脚本执行失败，继续..."
else
    info_msg "创建默认 Nginx 配置..."
    sudo tee /etc/nginx/sites-available/aikz.usdt2026.cc > /dev/null <<EOF
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # 启用配置
    sudo ln -sf /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
fi

# 测试 Nginx 配置
sudo nginx -t || error_exit "Nginx 配置测试失败"
success_msg "Nginx 配置完成"
echo ""

# 步骤 7: 修复文件权限
echo "[7/10] 修复文件权限..."
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR" || true
success_msg "文件权限已修复"
echo ""

# 步骤 8: 启用并启动服务
echo "[8/10] 启用并启动服务..."

# 启用服务（开机自启）
sudo systemctl enable luckyred-api
sudo systemctl enable liaotian-frontend

# 启动服务
sudo systemctl start luckyred-api
sleep 3
sudo systemctl start liaotian-frontend
sleep 3
sudo systemctl start nginx
sleep 2

success_msg "服务已启动"
echo ""

# 步骤 9: 验证服务状态
echo "[9/10] 验证服务状态..."

check_service() {
    local service=$1
    if sudo systemctl is-active --quiet "$service"; then
        success_msg "$service 正在运行"
        return 0
    else
        error_exit "$service 未运行"
        return 1
    fi
}

check_service "luckyred-api"
check_service "liaotian-frontend"
check_service "nginx"
echo ""

# 步骤 10: 健康检查
echo "[10/10] 执行健康检查..."

# 等待服务完全启动
sleep 5

# 检查后端健康
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    success_msg "后端健康检查通过 (HTTP $BACKEND_HEALTH)"
else
    info_msg "后端健康检查失败 (HTTP $BACKEND_HEALTH)，请查看日志: sudo journalctl -u luckyred-api -n 50"
fi

# 检查前端健康
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "304" ]; then
    success_msg "前端服务响应正常 (HTTP $FRONTEND_HEALTH)"
else
    info_msg "前端服务响应异常 (HTTP $FRONTEND_HEALTH)，请查看日志: sudo journalctl -u liaotian-frontend -n 50"
fi

# 检查端口监听
echo ""
info_msg "端口监听状态:"
sudo ss -tlnp | grep -E ':3000|:8000|:443' || info_msg "部分端口未监听"

echo ""
echo "========================================="
echo "部署完成！"
echo "========================================="
echo ""
echo "服务状态:"
echo "  后端: sudo systemctl status luckyred-api"
echo "  前端: sudo systemctl status liaotian-frontend"
echo "  Nginx: sudo systemctl status nginx"
echo ""
echo "查看日志:"
echo "  后端: sudo journalctl -u luckyred-api -f"
echo "  前端: sudo journalctl -u liaotian-frontend -f"
echo ""
echo "访问地址:"
echo "  HTTP: http://aikz.usdt2026.cc"
echo "  HTTPS: https://aikz.usdt2026.cc (如果已配置 SSL)"
echo ""
