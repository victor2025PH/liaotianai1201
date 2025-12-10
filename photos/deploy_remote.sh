#!/bin/bash
set -e

# ================= 配置区 =================
GIT_REPO="https://github.com/victor2025PH/liaotianai1201.git"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
DOMAIN="aikz.usdt2026.cc"
NODE_VERSION="20"
# =========================================

echo "🚀 开始全自动部署..."

# 1. 基础环境检查与 Swap 配置 (防止构建 OOM)
echo ">>> [1/5] 配置 Swap (4GB)..."
if ! grep -q "swapfile" /proc/swaps; then
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap 创建成功"
else
    echo "✅ Swap 已存在"
fi

# 2. 安装 Node.js (如果没装的话)
echo ">>> [2/5] 检查 Node.js 环境..."
export NVM_DIR="$HOME/.nvm"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
    echo "安装 nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
fi
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install $NODE_VERSION
nvm use $NODE_VERSION
nvm alias default $NODE_VERSION
echo "✅ Node.js $(node -v) 准备就绪"

# 3. 拉取代码
echo ">>> [3/5] 拉取代码..."
# 确保父目录存在
mkdir -p $(dirname "$PROJECT_DIR")

if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  目录已存在，尝试更新..."
    cd "$PROJECT_DIR"
    git pull origin main
else
    git clone "$GIT_REPO" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# 4. 构建前端 (最耗时的一步)
echo ">>> [4/5] 构建前端..."
cd saas-demo
# 设置内存限制，防止 OOM
export NODE_OPTIONS="--max-old-space-size=3072"

echo "安装依赖..."
npm install --production=false

echo "开始构建..."
npm run build

# 检查 Standalone
if [ ! -d ".next/standalone" ]; then
    echo "❌ 构建失败：未生成 standalone 目录！"
    exit 1
fi

# 复制静态资源 (Standalone 模式必须)
echo "准备运行文件..."
cp -r .next/static .next/standalone/.next/
cp -r public .next/standalone/

# 5. 配置 Systemd 服务
echo ">>> [5/5] 配置 Systemd 服务..."
# 获取当前使用的 node 绝对路径
NODE_PATH=$(which node)

sudo bash -c "cat > /etc/systemd/system/liaotian-frontend.service <<EOF
[Unit]
Description=Liaotian Frontend (Next.js Standalone)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR/saas-demo/.next/standalone
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=2048
ExecStart=$NODE_PATH server.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable liaotian-frontend.service
sudo systemctl restart liaotian-frontend.service

# 6. 配置 Nginx
echo ">>> [6/6] 配置 Nginx..."
sudo bash -c "cat > /etc/nginx/sites-available/aikz.conf <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF"

sudo ln -sf /etc/nginx/sites-available/aikz.conf /etc/nginx/sites-enabled/aikz.conf
# 移除可能存在的默认配置或旧配置
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/liaotian*
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "🎉====================================================🎉"
echo "   部署完成！"
echo "   前端地址: http://$DOMAIN"
echo "   服务状态: sudo systemctl status liaotian-frontend"
echo "🎉====================================================🎉"