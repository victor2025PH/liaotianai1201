#!/bin/bash
# 初始部署脚本 - 适用于全新的服务器或项目目录不存在的情况

set -e  # 遇到错误立即退出

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
GITHUB_REPO="https://github.com/victor2025PH/liaotianai1201.git"

echo "========================================="
echo "初始部署脚本 - 全新服务器部署"
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

# 步骤 1: 安装基本依赖
echo "[1/8] 安装基本依赖..."
sudo apt-get update -qq
sudo apt-get install -y git curl wget python3 python3-venv python3-pip nginx || error_exit "安装基本依赖失败"

# 安装 Node.js 20（Next.js 16 需要 Node.js >= 20.9.0）
info_msg "安装 Node.js 20..."
if command -v node &> /dev/null; then
    CURRENT_NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$CURRENT_NODE_VERSION" -lt 20 ]; then
        info_msg "当前 Node.js 版本过低 ($(node --version))，正在升级到 Node.js 20..."
        # 卸载旧版本
        sudo apt-get remove -y nodejs npm 2>/dev/null || true
    fi
fi

# 使用 NodeSource 安装 Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - || error_exit "NodeSource 仓库添加失败"
sudo apt-get install -y nodejs || error_exit "Node.js 20 安装失败"

# 验证 Node.js 版本
NODE_VERSION=$(node --version)
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_MAJOR" -lt 20 ]; then
    error_exit "Node.js 版本仍然不足 20，当前版本: $NODE_VERSION"
fi
success_msg "Node.js 安装成功: $NODE_VERSION"
success_msg "基本依赖安装完成"
echo ""

# 步骤 2: 克隆项目
echo "[2/8] 克隆项目代码..."
if [ -d "$PROJECT_DIR" ]; then
    info_msg "项目目录已存在，先删除..."
    sudo rm -rf "$PROJECT_DIR"
fi

sudo mkdir -p "$(dirname "$PROJECT_DIR")"
sudo chown -R ubuntu:ubuntu "$(dirname "$PROJECT_DIR")"

cd "$(dirname "$PROJECT_DIR")"
info_msg "正在从 GitHub 克隆项目（这可能需要几分钟）..."
git clone "$GITHUB_REPO" "$(basename "$PROJECT_DIR")" || error_exit "Git clone 失败"

cd "$PROJECT_DIR"
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR"
success_msg "项目代码克隆完成"
echo ""

# 步骤 3: 配置后端
echo "[3/8] 配置后端..."
cd "$PROJECT_DIR/admin-backend"

# 创建 Python 虚拟环境
info_msg "创建 Python 虚拟环境..."
python3 -m venv venv || error_exit "创建虚拟环境失败"

# 激活虚拟环境并安装依赖
source venv/bin/activate
info_msg "安装后端依赖（这可能需要几分钟）..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet || error_exit "安装后端依赖失败"
success_msg "后端配置完成"
echo ""

# 步骤 4: 配置前端
echo "[4/8] 配置前端..."
cd "$PROJECT_DIR/saas-demo"

info_msg "安装前端依赖（这可能需要几分钟）..."
npm install --prefer-offline --no-audit --no-fund || error_exit "安装前端依赖失败"

# 构建前端
info_msg "构建前端（这可能需要5-10分钟）..."
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build || error_exit "前端构建失败"

# 复制静态资源（Next.js standalone 模式需要）
info_msg "处理静态资源..."
mkdir -p .next/standalone/.next/static || true
cp -r .next/static/* .next/standalone/.next/static/ 2>/dev/null || true
cp -r public .next/standalone/ 2>/dev/null || true

success_msg "前端配置完成"
echo ""

# 步骤 5: 配置 systemd 服务
echo "[5/8] 配置 systemd 服务..."

# 复制服务文件
if [ -f "$PROJECT_DIR/deploy/systemd/luckyred-api.service" ]; then
    sudo cp "$PROJECT_DIR/deploy/systemd/luckyred-api.service" /etc/systemd/system/
    success_msg "后端服务文件已复制"
else
    info_msg "创建后端服务文件..."
    sudo tee /etc/systemd/system/luckyred-api.service > /dev/null <<EOF
[Unit]
Description=LuckyRed API Service (FastAPI)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR/admin-backend
Environment="PATH=$PROJECT_DIR/admin-backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONPATH=$PROJECT_DIR/admin-backend"
ExecStart=$PROJECT_DIR/admin-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
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
    success_msg "后端服务文件已创建"
fi

if [ -f "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" ]; then
    sudo cp "$PROJECT_DIR/deploy/systemd/liaotian-frontend.service" /etc/systemd/system/
    success_msg "前端服务文件已复制"
else
    info_msg "创建前端服务文件..."
    sudo tee /etc/systemd/system/liaotian-frontend.service > /dev/null <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR/saas-demo
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
ExecStart=/usr/bin/node .next/standalone/saas-demo/server.js
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
echo "[6/8] 配置 Nginx..."

# 创建 Nginx 配置
info_msg "创建 Nginx 配置..."
sudo tee /etc/nginx/sites-available/aikz.usdt2026.cc > /dev/null <<EOF
server {
    listen 80;
    server_name aikz.usdt2026.cc;

    # Workers API（专门处理，放在最前面）
    location ~ ^/api/workers(/.*)?$ {
        proxy_pass http://127.0.0.1:8000/api/v1/workers\$1;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 后端所有 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
    }

    # 前端应用
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    # 后端健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
EOF

# 启用配置
sudo ln -sf /etc/nginx/sites-available/aikz.usdt2026.cc /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# 测试 Nginx 配置
sudo nginx -t || error_exit "Nginx 配置测试失败"
success_msg "Nginx 配置完成"
echo ""

# 步骤 7: 修复文件权限
echo "[7/8] 修复文件权限..."
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR"
success_msg "文件权限已修复"
echo ""

# 步骤 8: 启用并启动服务
echo "[8/8] 启用并启动服务..."

# 启用服务（开机自启）
sudo systemctl enable luckyred-api
sudo systemctl enable liaotian-frontend

# 启动服务
sudo systemctl start luckyred-api
sleep 5
sudo systemctl start liaotian-frontend
sleep 5
sudo systemctl start nginx
sleep 3

success_msg "服务已启动"
echo ""

# 验证服务状态
echo "========================================="
echo "验证服务状态"
echo "========================================="
echo ""

check_service() {
    local service=$1
    if sudo systemctl is-active --quiet "$service"; then
        success_msg "$service 正在运行"
        return 0
    else
        echo -e "${RED}❌ $service 未运行${NC}"
        echo "查看日志: sudo journalctl -u $service -n 30 --no-pager"
        return 1
    fi
}

check_service "luckyred-api"
check_service "liaotian-frontend"
check_service "nginx"
echo ""

# 健康检查
echo "执行健康检查..."
sleep 5

BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    success_msg "后端健康检查通过 (HTTP $BACKEND_HEALTH)"
else
    info_msg "后端健康检查失败 (HTTP $BACKEND_HEALTH)"
fi

FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "304" ]; then
    success_msg "前端服务响应正常 (HTTP $FRONTEND_HEALTH)"
else
    info_msg "前端服务响应异常 (HTTP $FRONTEND_HEALTH)"
fi

echo ""
echo "========================================="
echo "初始部署完成！"
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
