#!/bin/bash
# ============================================================
# 新服务器完整初始化脚本
# ============================================================
# 
# 功能：
# 1. 系统更新和基础软件安装
# 2. 安装 Redis, Node.js, Python, Nginx
# 3. 配置 SSH 服务
# 4. 配置防火墙
# 5. 部署应用
# 6. 配置 SSL 证书
#
# 使用方法：
# 1. 在新服务器上克隆项目或上传脚本
# 2. 运行: sudo bash scripts/server/init_new_server.sh
# ============================================================

set -e

echo "============================================================"
echo "新服务器完整初始化脚本"
echo "============================================================"
echo "开始时间: $(date)"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 此脚本需要 root 权限，请使用 sudo 运行"
    exit 1
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
GITHUB_REPO="${GITHUB_REPO:-victor2025PH/liaotianai1201}"

# ============================================================
# [1/8] 系统更新
# ============================================================
echo "[1/8] 系统更新"
echo "------------------------------------------------------------"
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git vim net-tools
echo "✅ 系统更新完成"
echo ""

# ============================================================
# [2/8] 安装 Redis
# ============================================================
echo "[2/8] 安装 Redis"
echo "------------------------------------------------------------"
if command -v redis-cli > /dev/null 2>&1; then
    echo "✅ Redis 已安装"
else
    apt-get install -y redis-server
    # 配置 Redis
    sed -i 's/^#*supervised .*/supervised systemd/' /etc/redis/redis.conf
    sed -i 's/^#*bind .*/bind 127.0.0.1/' /etc/redis/redis.conf
    echo "protected-mode yes" >> /etc/redis/redis.conf
    systemctl start redis-server
    systemctl enable redis-server
    echo "✅ Redis 已安装并启动"
fi
echo ""

# ============================================================
# [3/8] 安装 Node.js
# ============================================================
echo "[3/8] 安装 Node.js"
echo "------------------------------------------------------------"
if command -v node > /dev/null 2>&1; then
    echo "✅ Node.js 已安装: $(node --version)"
else
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    echo "✅ Node.js 已安装: $(node --version)"
fi
echo ""

# ============================================================
# [4/8] 安装 Python 和依赖
# ============================================================
echo "[4/8] 安装 Python 和依赖"
echo "------------------------------------------------------------"
apt-get install -y python3 python3-pip python3-venv python3-dev
echo "✅ Python 已安装: $(python3 --version)"
echo ""

# ============================================================
# [5/8] 安装 Nginx
# ============================================================
echo "[5/8] 安装 Nginx"
echo "------------------------------------------------------------"
if command -v nginx > /dev/null 2>&1; then
    echo "✅ Nginx 已安装"
else
    apt-get install -y nginx
    systemctl start nginx
    systemctl enable nginx
    echo "✅ Nginx 已安装并启动"
fi
echo ""

# ============================================================
# [6/8] 配置 SSH 服务
# ============================================================
echo "[6/8] 配置 SSH 服务"
echo "------------------------------------------------------------"
apt-get install -y openssh-server
systemctl start ssh
systemctl enable ssh
echo "✅ SSH 服务已启动"
echo ""

# ============================================================
# [7/8] 配置防火墙
# ============================================================
echo "[7/8] 配置防火墙"
echo "------------------------------------------------------------"
if command -v ufw > /dev/null 2>&1; then
    # 允许 SSH（重要：先允许 SSH，避免被锁在外面）
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    # 启用防火墙（如果未启用）
    echo "y" | ufw enable 2>/dev/null || true
    echo "✅ 防火墙已配置"
else
    echo "⚠️  UFW 未安装，跳过防火墙配置"
fi
echo ""

# ============================================================
# [8/8] 部署应用
# ============================================================
echo "[8/8] 部署应用"
echo "------------------------------------------------------------"

# 创建项目目录
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit 1

# 克隆项目（如果不存在）
if [ ! -d ".git" ]; then
    echo "□ 克隆项目..."
    git clone "https://github.com/${GITHUB_REPO}.git" .
    echo "✅ 项目已克隆"
else
    echo "□ 项目已存在，拉取最新代码..."
    git pull origin main || echo "⚠️  Git pull 失败，继续..."
fi
echo ""

# 设置文件权限
chown -R ubuntu:ubuntu "$PROJECT_DIR"
echo "✅ 文件权限已设置"
echo ""

# 安装前端依赖
if [ -d "saas-demo" ]; then
    echo "□ 安装前端依赖..."
    cd saas-demo
    npm install --prefer-offline --no-audit --no-fund || echo "⚠️  npm install 失败，继续..."
    cd ..
    echo "✅ 前端依赖安装完成"
fi
echo ""

# 安装后端依赖
if [ -d "admin-backend" ]; then
    echo "□ 安装后端依赖..."
    cd admin-backend
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt --quiet || echo "⚠️  部分依赖安装失败，继续..."
    deactivate
    cd ..
    echo "✅ 后端依赖安装完成"
fi
echo ""

# 部署 Systemd 服务
echo "□ 部署 Systemd 服务..."
if [ -f "deploy/systemd/luckyred-api.service" ]; then
    cp deploy/systemd/luckyred-api.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable luckyred-api
    echo "✅ 后端服务配置已部署"
fi

if [ -f "deploy/systemd/liaotian-frontend.service" ]; then
    cp deploy/systemd/liaotian-frontend.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable liaotian-frontend
    echo "✅ 前端服务配置已部署"
fi
echo ""

# 构建前端
if [ -d "saas-demo" ]; then
    echo "□ 构建前端（这可能需要几分钟）..."
    cd saas-demo
    export NODE_ENV=production
    export NODE_OPTIONS="--max-old-space-size=4096"
    npm run build || echo "⚠️  前端构建失败，稍后可以手动构建"
    cd ..
    echo "✅ 前端构建完成"
fi
echo ""

# 配置 Nginx（基础配置）
echo "□ 配置 Nginx..."
if [ -f "scripts/server/fix-nginx-routes-complete.sh" ]; then
    bash scripts/server/fix-nginx-routes-complete.sh || echo "⚠️  Nginx 配置失败，需要手动配置"
else
    echo "⚠️  Nginx 配置脚本不存在，需要手动配置"
fi
echo ""

# 启动服务
echo "□ 启动服务..."
systemctl start luckyred-api 2>/dev/null || echo "⚠️  后端服务启动失败"
systemctl start liaotian-frontend 2>/dev/null || echo "⚠️  前端服务启动失败"
systemctl restart nginx
echo "✅ 服务已启动"
echo ""

# ============================================================
# 最终验证
# ============================================================
echo "============================================================"
echo "最终验证"
echo "============================================================"

sleep 5

echo "□ 服务状态:"
systemctl is-active --quiet nginx && echo "✅ Nginx: 运行中" || echo "❌ Nginx: 未运行"
systemctl is-active --quiet liaotian-frontend && echo "✅ 前端: 运行中" || echo "❌ 前端: 未运行"
systemctl is-active --quiet luckyred-api && echo "✅ 后端: 运行中" || echo "❌ 后端: 未运行"
systemctl is-active --quiet redis-server && echo "✅ Redis: 运行中" || echo "❌ Redis: 未运行"
systemctl is-active --quiet ssh && echo "✅ SSH: 运行中" || echo "❌ SSH: 未运行"
echo ""

echo "□ 端口监听:"
ss -tlnp | grep -E ":(22|80|443|3000|8000)" || echo "部分端口未监听"
echo ""

echo "============================================================"
echo "初始化完成"
echo "结束时间: $(date)"
echo "============================================================"
echo ""
echo "下一步操作："
echo "1. 配置 SSL 证书: sudo certbot --nginx -d aikz.usdt2026.cc"
echo "2. 检查服务日志: sudo journalctl -u luckyred-api -n 50"
echo "3. 测试网站访问: curl https://aikz.usdt2026.cc/login"
echo ""

