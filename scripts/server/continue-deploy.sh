#!/bin/bash
# 继续部署脚本 - 在 Node.js 升级后继续完成部署

set -e  # 遇到错误立即退出

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

echo "========================================="
echo "继续完成部署"
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

# 验证 Node.js 版本
echo "[检查] 验证 Node.js 版本..."
NODE_VERSION=$(node --version)
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_MAJOR" -lt 20 ]; then
    error_exit "Node.js 版本不足 20，当前版本: $NODE_VERSION，请先升级 Node.js"
fi
success_msg "Node.js 版本符合要求: $NODE_VERSION"
echo ""

# 步骤 1: 配置前端
echo "[1/5] 配置前端..."
cd "$FRONTEND_DIR" || error_exit "无法进入前端目录: $FRONTEND_DIR"

info_msg "安装前端依赖..."
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

# 步骤 2: 配置 systemd 服务
echo "[2/5] 配置 systemd 服务..."

cd "$PROJECT_DIR"

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

# 步骤 3: 配置 Nginx
echo "[3/5] 配置 Nginx..."

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

# 步骤 4: 修复文件权限
echo "[4/5] 修复文件权限..."
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR"
success_msg "文件权限已修复"
echo ""

# 步骤 5: 启用并启动服务
echo "[5/5] 启用并启动服务..."

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
    info_msg "后端健康检查失败 (HTTP $BACKEND_HEALTH)，请查看日志: sudo journalctl -u luckyred-api -n 50"
fi

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
