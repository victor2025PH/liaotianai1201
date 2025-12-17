#!/bin/bash
# ============================================================
# Ubuntu 22.04 LTS 完整初始化部署脚本（使用 PM2）
# ============================================================
# 
# 功能：
# 1. 系统防死机配置（Swap 8GB + 网络固化）
# 2. 环境安装（Python 3.10, Node.js LTS, Nginx, PM2）
# 3. 项目部署（GitHub 拉取 + PM2 配置）
# 
# 使用方法：
#   chmod +x scripts/server/initial-deploy-ubuntu22-pm2.sh
#   sudo bash scripts/server/initial-deploy-ubuntu22-pm2.sh
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
step_msg() { echo -e "${BLUE}📌 $1${NC}"; }

# 项目配置
PROJECT_DIR="/home/ubuntu/telegram-ai-system"
GITHUB_REPO="https://github.com/victor2025PH/liaotianai1201.git"
SWAP_SIZE_GB=8
SWAP_FILE="/swapfile"

echo "========================================="
echo "Ubuntu 22.04 LTS 完整初始化部署"
echo "使用 PM2 进程管理器"
echo "========================================="
echo ""

# 检查是否以 root 或 sudo 权限运行
if [ "$EUID" -ne 0 ]; then 
    error_msg "请使用 sudo 运行此脚本"
    exit 1
fi

# ============================================================
# 第一部分：系统防死机配置（优先级最高）
# ============================================================
echo "========================================="
echo "第一部分：系统防死机配置"
echo "========================================="
echo ""

# 1. 创建 8GB Swap 文件
step_msg "[1/2] 创建 8GB Swap 文件..."

if [ -f "$SWAP_FILE" ]; then
    info_msg "Swap 文件已存在，检查大小..."
    CURRENT_SWAP_SIZE=$(du -h "$SWAP_FILE" | awk '{print $1}')
    info_msg "当前 Swap 大小: $CURRENT_SWAP_SIZE"
    
    # 检查是否已挂载
    if swapon --show | grep -q "$SWAP_FILE"; then
        success_msg "Swap 已挂载，跳过创建"
    else
        info_msg "Swap 文件存在但未挂载，正在挂载..."
        swapon "$SWAP_FILE" || true
        success_msg "Swap 已挂载"
    fi
else
    info_msg "创建 ${SWAP_SIZE_GB}GB Swap 文件（这可能需要几分钟）..."
    fallocate -l ${SWAP_SIZE_GB}G "$SWAP_FILE"
    chmod 600 "$SWAP_FILE"
    mkswap "$SWAP_FILE"
    swapon "$SWAP_FILE"
    success_msg "Swap 文件创建并挂载成功"
fi

# 添加到 /etc/fstab 实现开机自动挂载
if ! grep -q "$SWAP_FILE" /etc/fstab; then
    echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab
    success_msg "Swap 已添加到 /etc/fstab（开机自动挂载）"
else
    info_msg "Swap 已在 /etc/fstab 中"
fi

# 验证 Swap
SWAP_TOTAL=$(free -h | grep Swap | awk '{print $2}')
success_msg "Swap 总大小: $SWAP_TOTAL"
echo ""

# 2. 检查和固化网络配置（Netplan）
step_msg "[2/2] 检查和固化网络配置..."

# Ubuntu 22.04 使用 Netplan
if [ -d "/etc/netplan" ]; then
    NETPLAN_FILE=$(ls /etc/netplan/*.yaml 2>/dev/null | head -1)
    
    if [ -n "$NETPLAN_FILE" ]; then
        info_msg "找到 Netplan 配置文件: $NETPLAN_FILE"
        
        # 检查配置是否包含 DHCP 或静态 IP
        if grep -q "dhcp4: true" "$NETPLAN_FILE"; then
            success_msg "网络配置使用 DHCP（自动获取 IP）"
        elif grep -q "addresses:" "$NETPLAN_FILE"; then
            success_msg "网络配置使用静态 IP"
        fi
        
        # 测试 Netplan 配置
        if netplan try --timeout 5 2>/dev/null; then
            success_msg "Netplan 配置有效"
        else
            info_msg "Netplan 配置测试完成"
        fi
    else
        info_msg "未找到 Netplan 配置文件，使用默认配置"
    fi
else
    info_msg "未找到 /etc/netplan 目录（可能不是 Ubuntu 22.04）"
fi

# 检查网络连接
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    success_msg "网络连接正常"
else
    error_msg "网络连接失败，请检查网络配置"
fi
echo ""

# ============================================================
# 第二部分：安装环境
# ============================================================
echo "========================================="
echo "第二部分：安装环境"
echo "========================================="
echo ""

# 1. 更新 apt 源
step_msg "[1/5] 更新 apt 源..."
export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y
success_msg "apt 源更新完成"
echo ""

# 2. 安装基础工具
step_msg "[2/5] 安装基础工具..."
apt install -y curl wget git build-essential software-properties-common \
    ca-certificates gnupg lsb-release
success_msg "基础工具安装完成"
echo ""

# 3. 安装 Python 3.10 和相关工具
step_msg "[3/5] 安装 Python 3.10、pip、venv..."

# Ubuntu 22.04 自带 Python 3.10
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
if [ "$PYTHON_VERSION" = "3.10" ] || [ "$PYTHON_VERSION" \> "3.10" ]; then
    success_msg "Python 3.10+ 已安装: $(python3 --version)"
else
    error_msg "Python 版本过低: $(python3 --version)"
    exit 1
fi

# 安装 pip 和 venv
apt install -y python3-pip python3-venv python3-dev
python3 -m pip install --upgrade pip setuptools wheel

# 验证
pip3 --version
python3 -m venv --help > /dev/null 2>&1 && success_msg "Python 环境配置完成"
echo ""

# 4. 安装 Node.js (LTS)
step_msg "[4/5] 安装 Node.js LTS..."

# 检查 Node.js 是否已安装
if command -v node > /dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    info_msg "Node.js 已安装: $NODE_VERSION"
    
    # 检查版本是否符合要求（需要 >= 20.9.0）
    NODE_MAJOR=$(echo $NODE_VERSION | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 20 ]; then
        success_msg "Node.js 版本符合要求: $NODE_VERSION"
    else
        info_msg "Node.js 版本过低，准备升级到 LTS..."
        # 卸载旧版本
        apt remove -y nodejs npm || true
    fi
fi

# 安装 Node.js LTS (从 NodeSource)
if ! command -v node > /dev/null 2>&1 || [ "$NODE_MAJOR" -lt 20 ]; then
    info_msg "从 NodeSource 安装 Node.js LTS..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt install -y nodejs
    
    # 验证
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    success_msg "Node.js 安装完成: $NODE_VERSION"
    success_msg "npm 版本: $NPM_VERSION"
else
    NPM_VERSION=$(npm --version)
    info_msg "npm 版本: $NPM_VERSION"
fi
echo ""

# 5. 安装 Nginx
step_msg "[5/5] 安装 Nginx..."
apt install -y nginx
systemctl enable nginx
systemctl start nginx

if systemctl is-active --quiet nginx; then
    success_msg "Nginx 安装并启动成功"
else
    error_msg "Nginx 启动失败"
    exit 1
fi
echo ""

# 6. 全局安装 PM2
step_msg "[额外] 全局安装 PM2..."
npm install -g pm2@latest

# 验证 PM2
PM2_VERSION=$(pm2 --version)
success_msg "PM2 安装完成: v$PM2_VERSION"
echo ""

# ============================================================
# 第三部分：部署项目
# ============================================================
echo "========================================="
echo "第三部分：部署项目"
echo "========================================="
echo ""

# 1. 创建项目目录并拉取代码
step_msg "[1/4] 拉取项目代码..."

# 切换到 ubuntu 用户的主目录
cd /home/ubuntu

# 检查项目目录是否存在
if [ -d "$PROJECT_DIR" ]; then
    info_msg "项目目录已存在，更新代码..."
    cd "$PROJECT_DIR"
    git fetch origin main || true
    git reset --hard origin/main || true
else
    info_msg "克隆项目代码..."
    git clone "$GITHUB_REPO" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

success_msg "项目代码准备完成"
echo ""

# 2. 设置项目目录权限
step_msg "[2/4] 设置项目目录权限..."
chown -R ubuntu:ubuntu "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
success_msg "目录权限设置完成"
echo ""

# 3. 安装后端依赖
step_msg "[3/4] 安装后端依赖..."

cd "$PROJECT_DIR/admin-backend"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    info_msg "创建 Python 虚拟环境..."
    sudo -u ubuntu python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

success_msg "后端依赖安装完成"
deactivate
echo ""

# 4. 安装前端依赖并构建
step_msg "[4/4] 安装前端依赖并构建..."

cd "$PROJECT_DIR/saas-demo"

# 安装依赖
sudo -u ubuntu npm install --prefer-offline --no-audit

# 构建前端（standalone 模式）
info_msg "构建前端（这可能需要几分钟）..."
sudo -u ubuntu npm run build

# 验证构建结果
if [ -d ".next/standalone" ]; then
    success_msg "前端构建完成（standalone 模式）"
else
    error_msg "前端构建失败，.next/standalone 目录不存在"
    exit 1
fi

# 复制静态资源（standalone 模式需要）
if [ -d ".next/static" ]; then
    mkdir -p .next/standalone/.next/static
    cp -r .next/static/* .next/standalone/.next/static/ || true
    cp -r public .next/standalone/ || true
    success_msg "静态资源复制完成"
fi
echo ""

# ============================================================
# 第四部分：配置 PM2
# ============================================================
echo "========================================="
echo "第四部分：配置 PM2"
echo "========================================="
echo ""

step_msg "[1/2] 生成 ecosystem.config.js..."

# 切换到 ubuntu 用户执行 PM2 相关操作
cd "$PROJECT_DIR"

# 创建 logs 目录
mkdir -p logs
chown ubuntu:ubuntu logs

# 生成 ecosystem.config.js（如果不存在或需要更新）
ECOSYSTEM_FILE="$PROJECT_DIR/ecosystem.config.js"

cat > "$ECOSYSTEM_FILE" << 'EOF'
module.exports = {
  apps: [
    {
      name: "backend",
      cwd: "/home/ubuntu/telegram-ai-system/admin-backend",
      // 使用虚拟环境中的 uvicorn
      script: "/home/ubuntu/telegram-ai-system/admin-backend/venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        PORT: 8000,
        PYTHONPATH: "/home/ubuntu/telegram-ai-system/admin-backend",
        PYTHONUNBUFFERED: "1",
        NODE_ENV: "production"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/backend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/backend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      exec_mode: "fork"
    },
    {
      name: "frontend",
      cwd: "/home/ubuntu/telegram-ai-system/saas-demo",
      // Next.js 16 standalone 模式
      script: "/usr/bin/node",
      args: ".next/standalone/server.js",
      env: {
        PORT: 3000,
        NODE_ENV: "production",
        NODE_OPTIONS: "--max-old-space-size=1024"
      },
      error_file: "/home/ubuntu/telegram-ai-system/logs/frontend-error.log",
      out_file: "/home/ubuntu/telegram-ai-system/logs/frontend-out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      instances: 1,
      exec_mode: "fork"
    }
  ]
};
EOF

chown ubuntu:ubuntu "$ECOSYSTEM_FILE"
chmod 644 "$ECOSYSTEM_FILE"
success_msg "ecosystem.config.js 生成完成"
echo ""

# 5. 启动 PM2 应用
step_msg "[2/2] 启动 PM2 应用..."

# 切换到 ubuntu 用户执行 PM2
sudo -u ubuntu bash << 'PM2_SCRIPT'
cd /home/ubuntu/telegram-ai-system

# 停止现有应用（如果存在）
pm2 delete all 2>/dev/null || true

# 启动应用
pm2 start ecosystem.config.js

# 保存 PM2 进程列表
pm2 save

# 显示状态
pm2 status
PM2_SCRIPT

success_msg "PM2 应用启动完成"
echo ""

# 6. 设置 PM2 开机自启
step_msg "[额外] 设置 PM2 开机自启..."

# 生成 startup 脚本（需要 root 权限）
STARTUP_SCRIPT=$(sudo -u ubuntu pm2 startup systemd -u ubuntu --hp /home/ubuntu 2>&1 | grep "sudo" | tail -1)

if [ -n "$STARTUP_SCRIPT" ]; then
    info_msg "执行 PM2 startup 命令..."
    eval "$STARTUP_SCRIPT"
    success_msg "PM2 开机自启配置完成"
else
    info_msg "PM2 startup 可能已配置"
fi
echo ""

# ============================================================
# 第五部分：配置 Nginx
# ============================================================
echo "========================================="
echo "第五部分：配置 Nginx（可选）"
echo "========================================="
echo ""

info_msg "Nginx 配置需要根据您的域名手动设置"
info_msg "默认配置文件位置: /etc/nginx/sites-available/default"
info_msg "建议配置："
echo ""
echo "  upstream backend {"
echo "      server 127.0.0.1:8000;"
echo "  }"
echo ""
echo "  upstream frontend {"
echo "      server 127.0.0.1:3000;"
echo "  }"
echo ""
echo "  server {"
echo "      listen 80;"
echo "      server_name your-domain.com;"
echo ""
echo "      location /api/ {"
echo "          proxy_pass http://backend;"
echo "          proxy_set_header Host \$host;"
echo "          proxy_set_header X-Real-IP \$remote_addr;"
echo "      }"
echo ""
echo "      location / {"
echo "          proxy_pass http://frontend;"
echo "          proxy_set_header Host \$host;"
echo "          proxy_set_header X-Real-IP \$remote_addr;"
echo "      }"
echo "  }"
echo ""

# ============================================================
# 完成
# ============================================================
echo "========================================="
echo "✅ 初始化部署完成！"
echo "========================================="
echo ""
echo "📊 系统状态："
echo "  - Swap: $(free -h | grep Swap | awk '{print $2}')"
echo "  - Python: $(python3 --version)"
echo "  - Node.js: $(node --version)"
echo "  - PM2: v$(pm2 --version)"
echo ""
echo "🚀 服务状态："
sudo -u ubuntu pm2 status
echo ""
echo "📝 常用命令："
echo "  - 查看 PM2 状态: pm2 status"
echo "  - 查看日志: pm2 logs"
echo "  - 重启服务: pm2 restart all"
echo "  - 停止服务: pm2 stop all"
echo "  - 查看后端日志: pm2 logs backend"
echo "  - 查看前端日志: pm2 logs frontend"
echo ""
echo "🔍 验证服务："
echo "  - 后端健康检查: curl http://localhost:8000/health"
echo "  - 前端访问: curl http://localhost:3000"
echo ""
success_msg "部署完成！"
