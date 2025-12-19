#!/bin/bash

# 自动移除 Windows 换行符
sed -i 's/\r$//' "$0" 2>/dev/null || true

# 定义项目路径
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
GITHUB_REPO="${GITHUB_REPO:-victor2025PH/liaotianai1201}"

# --- 辅助函数：安全杀掉占用端口的进程 ---
kill_port_process() {
    local PORT=$1
    echo "🔍 检查端口 $PORT..."
    
    # 查找占用端口的 PID
    PIDS=$(sudo lsof -t -i:$PORT 2>/dev/null || echo "")
    
    if [ -z "$PIDS" ]; then
        echo "   ✅ 端口 $PORT 空闲"
        return 0
    fi
    
    for PID in $PIDS; do
        # 获取进程名
        PNAME=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
        
        # 保护关键系统进程
        if [[ "$PNAME" =~ ^(sshd|ssh|systemd|dbus|init)$ ]]; then
            echo "   ⚠️  跳过关键系统进程: $PNAME (PID: $PID)"
            continue
        fi
        
        echo "   🔪 正在杀掉进程: $PNAME (PID: $PID)..."
        sudo kill -9 $PID 2>/dev/null || true
    done
}

# ====================================================
# 1. 环境准备与 Swap 配置 (关键修复)
# ====================================================
echo "🚀 开始部署..."
echo "时间: $(date)"

# 遇到错误继续执行 (清理阶段)
set +e

# 检查并创建 Swap (如果不存在)
if [ ! -f /swapfile ]; then
    echo "🔧 检测到 Swap 文件不存在，正在创建 (2GB)..."
    sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap 创建并启用成功"
else
    echo "✅ Swap 文件已存在，尝试启用..."
    sudo swapon /swapfile 2>/dev/null || true
fi
free -h

# ====================================================
# 2. 代码更新
# ====================================================
# 开启错误检查，确保代码拉取成功
set -e 

# 检查目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "项目目录不存在，正在克隆..."
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown -R ubuntu:ubuntu "$PROJECT_DIR"
    cd /home/ubuntu
    sudo -u ubuntu git clone "https://github.com/$GITHUB_REPO.git" telegram-ai-system
fi

cd "$PROJECT_DIR" || exit 1
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR"

echo "📥 更新代码..."
sudo -u ubuntu git fetch origin main
sudo -u ubuntu git reset --hard origin/main

# ====================================================
# 3. 构建前端 (最耗资源步骤)
# ====================================================
echo "📦 构建前端..."
cd saas-demo
rm -f .next/lock

# 安装依赖
export NODE_OPTIONS="--max-old-space-size=1536"
npm install --prefer-offline --no-audit

# 构建
npm run build

# 处理静态资源
echo "📂 处理静态资源..."
STANDALONE_DIR=".next/standalone"
# 兼容性查找
if [ ! -d "$STANDALONE_DIR" ]; then
    STANDALONE_DIR=$(find .next/standalone -type f -name "server.js" 2>/dev/null | head -1 | xargs dirname 2>/dev/null)
fi

if [ -z "$STANDALONE_DIR" ] || [ ! -d "$STANDALONE_DIR" ]; then
    echo "❌ 构建失败：未找到 standalone 目录"
    exit 1
fi

# 确保目录结构完整
mkdir -p "$STANDALONE_DIR/.next/static"
mkdir -p "$STANDALONE_DIR/.next/server"
mkdir -p "$STANDALONE_DIR/.next"

# 复制 BUILD_ID（必需）
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID "$STANDALONE_DIR/.next/BUILD_ID" 2>/dev/null || true
    echo "✅ BUILD_ID 已复制"
fi

# 复制所有 JSON 配置文件（必需）
for json_file in .next/*.json; do
    if [ -f "$json_file" ]; then
        cp "$json_file" "$STANDALONE_DIR/.next/" 2>/dev/null || true
    fi
done
echo "✅ JSON 配置文件已复制"

# 复制 static 目录（必需）
if [ -d ".next/static" ]; then
    cp -r .next/static/* "$STANDALONE_DIR/.next/static/" 2>/dev/null || true
    echo "✅ static 目录已复制"
fi

# 复制 server 目录（必需，包含 pages-manifest.json 等）
if [ -d ".next/server" ]; then
    cp -r .next/server/* "$STANDALONE_DIR/.next/server/" 2>/dev/null || true
    echo "✅ server 目录已复制"
fi

# 复制 public 目录
if [ -d "public" ]; then
    cp -r public "$STANDALONE_DIR/" 2>/dev/null || true
    echo "✅ public 目录已复制"
fi

# 验证关键文件
if [ ! -f "$STANDALONE_DIR/.next/BUILD_ID" ]; then
    echo "⚠️  警告：BUILD_ID 未复制"
fi

if [ ! -f "$STANDALONE_DIR/.next/server/pages-manifest.json" ]; then
    echo "⚠️  警告：pages-manifest.json 未复制"
fi

cd ..

# ====================================================
# 4. 后端环境准备
# ====================================================
echo "🐍 准备后端..."
# 安装系统依赖 (忽略错误以防锁占用)
set +e
sudo DEBIAN_FRONTEND=noninteractive apt-get update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv python3-pip redis-server psmisc net-tools
sudo systemctl start redis-server
set -e

cd admin-backend
# 重建虚拟环境
rm -rf venv
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 生成 .env
if [ ! -f ".env" ]; then
    echo "JWT_SECRET=prod_secret_$(date +%s)" > .env
    echo "LOG_LEVEL=INFO" >> .env
    echo "DATABASE_URL=sqlite:///./admin.db" >> .env
fi
cd ..

# ====================================================
# 5. 清理旧服务 (使用 Set +e 模式)
# ====================================================
echo "🧹 清理旧服务..."
set +e

# 使用函数清理端口
kill_port_process 3000
kill_port_process 8000

# PM2 清理
sudo -u ubuntu pm2 delete all 2>/dev/null || true
sudo -u ubuntu pm2 flush 2>/dev/null || true

# 强制释放
sudo fuser -k -9 3000/tcp 2>/dev/null || true
sudo fuser -k -9 8000/tcp 2>/dev/null || true

echo "⏳ 等待端口释放..."
sleep 3

# ====================================================
# 6. 启动新服务
# ====================================================
echo "🚀 启动服务..."
set -e

# 确保所有权正确
sudo chown -R ubuntu:ubuntu "$PROJECT_DIR"

# 检查是否有 ecosystem.config.js，如果有则使用 PM2，否则使用 systemd
if [ -f "$PROJECT_DIR/ecosystem.config.js" ]; then
    # 使用 PM2 启动
    sudo -u ubuntu bash -c "cd $PROJECT_DIR && pm2 start ecosystem.config.js"
    sudo -u ubuntu bash -c "cd $PROJECT_DIR && pm2 save"
    
    echo "⏳ 等待服务初始化..."
    sleep 10
    
    # 检查状态
    sudo -u ubuntu pm2 list
else
    # 使用 systemd 启动
    echo "⚠️  未找到 ecosystem.config.js，使用 systemd 服务..."
    
    # 部署 systemd 服务
    if [ -f "scripts/server/deploy-systemd.sh" ]; then
        timeout 5m sudo bash scripts/server/deploy-systemd.sh || echo "⚠️  Systemd deployment failed or timeout, continuing..."
    fi
    
    # 重启后端服务
    BACKEND_SERVICE=""
    if systemctl cat luckyred-api.service >/dev/null 2>&1; then
        BACKEND_SERVICE="luckyred-api"
    elif systemctl cat telegram-backend.service >/dev/null 2>&1; then
        BACKEND_SERVICE="telegram-backend"
    fi
    
    if [ -n "$BACKEND_SERVICE" ]; then
        echo "重启后端服务: $BACKEND_SERVICE"
        timeout 10s sudo systemctl stop "$BACKEND_SERVICE" 2>/dev/null || true
        sleep 2
        timeout 30s sudo systemctl start "$BACKEND_SERVICE" && echo "✅ Backend ($BACKEND_SERVICE) restarted" || echo "⚠️  Backend restart failed or timeout"
    fi
    
    # 重启前端服务
    FRONTEND_SERVICE=""
    if systemctl cat liaotian-frontend.service >/dev/null 2>&1; then
        FRONTEND_SERVICE="liaotian-frontend"
    elif systemctl cat smart-tg-frontend.service >/dev/null 2>&1; then
        FRONTEND_SERVICE="smart-tg-frontend"
    fi
    
    if [ -n "$FRONTEND_SERVICE" ]; then
        echo "重启前端服务: $FRONTEND_SERVICE"
        timeout 10s sudo systemctl stop "$FRONTEND_SERVICE" 2>/dev/null || true
        sleep 2
        timeout 30s sudo systemctl start "$FRONTEND_SERVICE" && echo "✅ Frontend ($FRONTEND_SERVICE) restarted" || echo "⚠️  Frontend restart failed or timeout"
    fi
    
    echo "⏳ 等待服务初始化..."
    sleep 10
fi

# ====================================================
# 7. 更新 Nginx 配置（确保静态资源路径正确）
# ====================================================
echo "🌐 更新 Nginx 配置..."
set +e

NGINX_CONFIG="/etc/nginx/sites-available/aikz.usdt2026.cc"

# 如果使用仓库中的配置文件，复制并更新
if [ -f "$PROJECT_DIR/deploy/nginx/aikz.conf" ]; then
    echo "使用仓库中的 Nginx 配置..."
    sudo cp "$PROJECT_DIR/deploy/nginx/aikz.conf" "$NGINX_CONFIG"
    
    # 创建符号链接
    sudo ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/aikz.usdt2026.cc
    echo "✅ Nginx 配置已更新（包含 /next/static 和 /_next/static 路径支持）"
fi

# 测试 Nginx 配置
if sudo nginx -t 2>/dev/null; then
    echo "✅ Nginx 配置测试通过"
else
    echo "⚠️ Nginx 配置测试失败，但继续执行..."
    sudo nginx -t 2>&1 | head -10 || true
fi

set -e

# 重启 Nginx
echo "🔄 重启 Nginx..."
sudo systemctl restart nginx || echo "⚠️ Nginx 重启失败，请手动检查"

echo "🎉 部署完成！"
exit 0
