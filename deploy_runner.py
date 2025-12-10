import paramiko
import os

# 配置
HOST = '165.154.233.55'
USER = 'ubuntu'
# 如果已经配置了免密登录，不需要密码。如果没有，请填入密码。
# PASSWORD = 'Along2025!!!' 

# 你的部署脚本内容 (直接嵌在这里，避免 CRLF 问题)
DEPLOY_SCRIPT = r"""#!/bin/bash
set -e

# ================= 配置区 =================
GIT_REPO="https://github.com/victor2025PH/liaotianai1201.git"
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
DOMAIN="aikz.usdt2026.cc"
NODE_VERSION="20"
# =========================================

echo "🚀 开始全自动部署..."

# 1. 基础环境检查与 Swap 配置
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

# 2. 安装 Node.js
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

# 4. 构建前端
echo ">>> [4/5] 构建前端..."
cd saas-demo
export NODE_OPTIONS="--max-old-space-size=3072"

echo "安装依赖..."
npm install --production=false

echo "开始构建..."
npm run build

if [ ! -d ".next/standalone" ]; then
    echo "❌ 构建失败：未生成 standalone 目录！"
    exit 1
fi

echo "准备运行文件..."
cp -r .next/static .next/standalone/.next/
cp -r public .next/standalone/

# 5. 配置 Systemd 服务
echo ">>> [5/5] 配置 Systemd 服务..."
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
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "🎉====================================================🎉"
echo "   部署完成！"
echo "   前端地址: http://$DOMAIN"
echo "🎉====================================================🎉"
"""

# 将 Windows CRLF 换行符转换为 Linux LF
DEPLOY_SCRIPT = DEPLOY_SCRIPT.replace('\r\n', '\n')

print(f"正在连接 {HOST} ...")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 优先尝试免密登录
    try:
        client.connect(HOST, username=USER)
    except:
        # 如果免密失败，尝试密码登录（如果配置了密码）
        # client.connect(HOST, username=USER, password=PASSWORD)
        print("免密登录失败，请检查 SSH 配置")
        exit(1)
    
    print("正在上传并执行部署脚本...")
    
    # 写入脚本文件
    cmd = f"cat > /tmp/deploy.sh << 'END_SCRIPT'\n{DEPLOY_SCRIPT}\nEND_SCRIPT\n"
    cmd += "chmod +x /tmp/deploy.sh && bash /tmp/deploy.sh"
    
    # 执行命令并实时输出
    stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
    
    for line in iter(stdout.readline, ""):
        print(line, end="")
        
    client.close()

except Exception as e:
    print(f"❌ 发生错误: {e}")