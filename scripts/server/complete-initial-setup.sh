#!/bin/bash
# ============================================================
# Ubuntu 22.04 LTS 完整服务器初始化脚本
# ============================================================
# 
# 功能：
# 1. 基础环境安装（Node.js 20.x, Python 3.10+, Nginx, PM2）
# 2. 用户与权限配置（deployer 用户，SSH Key，无密码 sudo）
# 3. 项目目录结构
# 4. 防火墙与 SSH 连接优化（解决 Timeout 问题）
# 5. Nginx 基础配置框架
# 
# 使用方法：
#   curl -fsSL https://raw.githubusercontent.com/your-repo/main/scripts/server/complete-initial-setup.sh | sudo bash
#   或者：
#   chmod +x scripts/server/complete-initial-setup.sh
#   sudo bash scripts/server/complete-initial-setup.sh
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
step_msg() { echo -e "${BLUE}📌 $1${NC}"; }
section_msg() { echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${CYAN}$1${NC}"; echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# 配置变量
DEPLOYER_USER="deployer"
PROJECT_DIR="/home/${DEPLOYER_USER}/telegram-ai-system"
SSH_DIR="/home/${DEPLOYER_USER}/.ssh"
SWAP_SIZE_GB=8
SWAP_FILE="/swapfile"

echo ""
section_msg "Ubuntu 22.04 LTS 完整服务器初始化"
echo ""
info_msg "将创建用户: ${DEPLOYER_USER}"
info_msg "项目目录: ${PROJECT_DIR}"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    error_msg "请使用 sudo 运行此脚本"
    exit 1
fi

# ============================================================
# 第一部分：基础环境安装
# ============================================================
section_msg "第一部分：基础环境安装"

step_msg "更新 apt 源..."
export DEBIAN_FRONTEND=noninteractive
apt update -qq
apt upgrade -y -qq
success_msg "apt 源更新完成"

step_msg "安装常用工具 (curl, wget, git, unzip)..."
apt install -y -qq curl wget git unzip fail2ban
success_msg "常用工具安装完成"

step_msg "安装 Node.js 20.x LTS..."
# 使用 NodeSource 官方仓库
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null 2>&1
apt install -y -qq nodejs
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
success_msg "Node.js 安装完成: ${NODE_VERSION}, npm: ${NPM_VERSION}"

step_msg "安装 Python 3.10+ 和 pip..."
apt install -y -qq python3 python3-pip python3-venv python3-dev build-essential
PYTHON_VERSION=$(python3 --version)
PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
success_msg "Python 安装完成: ${PYTHON_VERSION}, pip: ${PIP_VERSION}"

step_msg "安装 Nginx..."
apt install -y -qq nginx
NGINX_VERSION=$(nginx -v 2>&1 | cut -d'/' -f2)
success_msg "Nginx 安装完成: ${NGINX_VERSION}"

step_msg "全局安装 PM2..."
npm install -g pm2 >/dev/null 2>&1
PM2_VERSION=$(pm2 --version)
success_msg "PM2 安装完成: ${PM2_VERSION}"

# ============================================================
# 第二部分：用户与权限配置
# ============================================================
section_msg "第二部分：用户与权限配置"

# 检查用户是否已存在
if id "$DEPLOYER_USER" &>/dev/null; then
    info_msg "用户 ${DEPLOYER_USER} 已存在，跳过创建"
else
    step_msg "创建用户 ${DEPLOYER_USER}..."
    useradd -m -s /bin/bash "${DEPLOYER_USER}"
    success_msg "用户 ${DEPLOYER_USER} 创建完成"
fi

step_msg "将 ${DEPLOYER_USER} 加入 sudo 组..."
usermod -aG sudo "${DEPLOYER_USER}"
success_msg "用户已加入 sudo 组"

step_msg "配置无密码 sudo..."
# 创建 sudoers.d 规则
SUDOERS_FILE="/etc/sudoers.d/${DEPLOYER_USER}"
cat > "${SUDOERS_FILE}" <<EOF
# 允许 ${DEPLOYER_USER} 无密码执行 sudo 命令
${DEPLOYER_USER} ALL=(ALL) NOPASSWD:ALL
EOF
chmod 0440 "${SUDOERS_FILE}"
success_msg "无密码 sudo 配置完成"

step_msg "配置 SSH 目录和权限..."
# 创建 .ssh 目录
mkdir -p "${SSH_DIR}"
chmod 700 "${SSH_DIR}"
chown "${DEPLOYER_USER}:${DEPLOYER_USER}" "${SSH_DIR}"

# 生成 SSH Key（如果不存在）
if [ ! -f "${SSH_DIR}/id_rsa" ]; then
    info_msg "生成 SSH Key..."
    sudo -u "${DEPLOYER_USER}" ssh-keygen -t rsa -b 4096 -f "${SSH_DIR}/id_rsa" -N "" -q
    success_msg "SSH Key 生成完成"
else
    info_msg "SSH Key 已存在，跳过生成"
fi

# 设置 authorized_keys（如果不存在）
if [ ! -f "${SSH_DIR}/authorized_keys" ]; then
    sudo -u "${DEPLOYER_USER}" cp "${SSH_DIR}/id_rsa.pub" "${SSH_DIR}/authorized_keys"
    chmod 600 "${SSH_DIR}/authorized_keys"
    chown "${DEPLOYER_USER}:${DEPLOYER_USER}" "${SSH_DIR}/authorized_keys"
    info_msg "已创建 authorized_keys（使用公钥内容）"
fi

success_msg "SSH 配置完成"

# ============================================================
# 第三部分：项目目录结构
# ============================================================
section_msg "第三部分：项目目录结构"

step_msg "创建项目目录 ${PROJECT_DIR}..."
mkdir -p "${PROJECT_DIR}"
chown -R "${DEPLOYER_USER}:${DEPLOYER_USER}" "${PROJECT_DIR}"
success_msg "项目目录创建完成"

# ============================================================
# 第四部分：防火墙与连接优化（解决 Timeout 问题）
# ============================================================
section_msg "第四部分：防火墙与 SSH 连接优化"

step_msg "配置 UFW 防火墙..."
# 确保 UFW 未启用时先重置
ufw --force reset 2>/dev/null || true

# 设置默认策略
ufw default deny incoming
ufw default allow outgoing

# 允许 SSH（关键！）
ufw allow OpenSSH comment 'Allow SSH'

# 允许 Nginx
ufw allow 'Nginx Full' comment 'Allow HTTP and HTTPS'

# 启用防火墙
ufw --force enable
success_msg "UFW 防火墙配置完成"

step_msg "优化 SSH 配置 (/etc/ssh/sshd_config)..."
SSH_CONFIG="/etc/ssh/sshd_config"
SSH_CONFIG_BACKUP="${SSH_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

# 备份原配置
cp "${SSH_CONFIG}" "${SSH_CONFIG_BACKUP}"
info_msg "已备份 SSH 配置到: ${SSH_CONFIG_BACKUP}"

# 配置 ClientAliveInterval 和 ClientAliveCountMax（防止空闲断开）
if ! grep -q "^ClientAliveInterval" "${SSH_CONFIG}"; then
    echo "ClientAliveInterval 60" >> "${SSH_CONFIG}"
else
    sed -i 's/^ClientAliveInterval.*/ClientAliveInterval 60/' "${SSH_CONFIG}"
fi

if ! grep -q "^ClientAliveCountMax" "${SSH_CONFIG}"; then
    echo "ClientAliveCountMax 3" >> "${SSH_CONFIG}"
else
    sed -i 's/^ClientAliveCountMax.*/ClientAliveCountMax 3/' "${SSH_CONFIG}"
fi

# 确保密码认证开启（暂时，配置好 Key 后可关闭）
if ! grep -q "^PasswordAuthentication" "${SSH_CONFIG}"; then
    echo "PasswordAuthentication yes" >> "${SSH_CONFIG}"
else
    sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' "${SSH_CONFIG}"
fi

# 确保公钥认证开启
if ! grep -q "^PubkeyAuthentication" "${SSH_CONFIG}"; then
    echo "PubkeyAuthentication yes" >> "${SSH_CONFIG}"
else
    sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' "${SSH_CONFIG}"
fi

# 重启 SSH 服务（Ubuntu 22.04 使用 ssh.service，不是 sshd.service）
if systemctl restart ssh 2>/dev/null; then
    success_msg "SSH 配置优化完成并已重启服务"
else
    # 如果 ssh.service 不存在，尝试 sshd.service（兼容性）
    if systemctl restart sshd 2>/dev/null; then
        success_msg "SSH 配置优化完成并已重启服务（使用 sshd.service）"
    else
        error_msg "无法重启 SSH 服务，请手动运行: sudo systemctl restart ssh"
        info_msg "SSH 配置已修改，但需要手动重启服务才能生效"
    fi
fi

# ============================================================
# 第五部分：Swap 文件（防止 OOM）
# ============================================================
section_msg "第五部分：创建 Swap 文件（防止内存溢出）"

if [ -f "${SWAP_FILE}" ]; then
    info_msg "Swap 文件已存在，跳过创建"
else
    step_msg "创建 ${SWAP_SIZE_GB}GB Swap 文件..."
    fallocate -l ${SWAP_SIZE_GB}G "${SWAP_FILE}" || dd if=/dev/zero of="${SWAP_FILE}" bs=1G count=${SWAP_SIZE_GB}
    chmod 600 "${SWAP_FILE}"
    mkswap "${SWAP_FILE}"
    swapon "${SWAP_FILE}"
    
    # 添加到 /etc/fstab 实现开机自动挂载
    if ! grep -q "${SWAP_FILE}" /etc/fstab; then
        echo "${SWAP_FILE} none swap sw 0 0" >> /etc/fstab
    fi
    
    success_msg "Swap 文件创建并启用完成"
fi

# 显示内存信息
echo ""
info_msg "当前内存状态："
free -h

# ============================================================
# 第六部分：Nginx 基础配置框架
# ============================================================
section_msg "第六部分：Nginx 基础配置框架"

step_msg "创建 Nginx 配置文件框架..."

NGINX_CONFIG="/etc/nginx/sites-available/telegram-ai-system"
NGINX_ENABLED="/etc/nginx/sites-enabled/telegram-ai-system"

cat > "${NGINX_CONFIG}" <<'EOF'
# Telegram AI System - Nginx 反向代理配置
# 前端: http://localhost:3000
# 后端: http://localhost:8000

server {
    listen 80;
    server_name _;  # 替换为您的域名，例如: example.com

    client_max_body_size 100M;

    # 前端代理
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket 支持（用于实时通知）
    location /api/v1/notifications/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 特殊设置
        proxy_buffering off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
EOF

# 禁用默认配置（如果存在）
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# 启用我们的配置
if [ -L "${NGINX_ENABLED}" ]; then
    rm "${NGINX_ENABLED}"
fi
ln -s "${NGINX_CONFIG}" "${NGINX_ENABLED}"

# 测试 Nginx 配置
if nginx -t >/dev/null 2>&1; then
    success_msg "Nginx 配置文件创建完成（已测试，语法正确）"
    # 不立即重启，等待用户部署项目后再重启
    info_msg "提示：部署项目后运行 'sudo systemctl restart nginx' 来应用配置"
else
    error_msg "Nginx 配置语法错误，请检查 ${NGINX_CONFIG}"
    # 恢复默认配置
    rm -f "${NGINX_ENABLED}"
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
fi

# ============================================================
# 第七部分：创建日志目录
# ============================================================
section_msg "第七部分：创建日志目录"

LOG_DIR="/home/${DEPLOYER_USER}/telegram-ai-system/logs"
mkdir -p "${LOG_DIR}"
chown -R "${DEPLOYER_USER}:${DEPLOYER_USER}" "${LOG_DIR}"
success_msg "日志目录创建完成: ${LOG_DIR}"

# ============================================================
# 完成总结
# ============================================================
echo ""
section_msg "🎉 服务器初始化完成！"
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}已完成以下配置：${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} 基础环境：Node.js ${NODE_VERSION}, Python ${PYTHON_VERSION}, Nginx ${NGINX_VERSION}, PM2 ${PM2_VERSION}"
echo -e "  ${GREEN}✓${NC} 用户配置：${DEPLOYER_USER} (sudo 权限，SSH Key 已生成)"
echo -e "  ${GREEN}✓${NC} 项目目录：${PROJECT_DIR}"
echo -e "  ${GREEN}✓${NC} 防火墙：UFW 已启用（允许 SSH, HTTP, HTTPS）"
echo -e "  ${GREEN}✓${NC} SSH 优化：ClientAliveInterval 60（防止断开）"
echo -e "  ${GREEN}✓${NC} Swap 文件：${SWAP_SIZE_GB}GB"
echo -e "  ${GREEN}✓${NC} Nginx 配置：已创建反向代理框架"
echo ""

echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}下一步操作：${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "1. 切换到 ${DEPLOYER_USER} 用户："
echo -e "   ${CYAN}sudo su - ${DEPLOYER_USER}${NC}"
echo ""
echo "2. 克隆项目代码："
echo -e "   ${CYAN}cd ${PROJECT_DIR}${NC}"
echo -e "   ${CYAN}git clone <YOUR_REPO_URL> .${NC}"
echo ""
echo "3. 部署项目（参考项目文档）："
echo -e "   ${CYAN}# 安装依赖、构建、启动服务等${NC}"
echo ""
echo "4. 配置 SSH Key（用于 GitHub Actions）："
echo -e "   ${CYAN}# 查看公钥：cat ${SSH_DIR}/id_rsa.pub${NC}"
echo -e "   ${CYAN}# 添加到 GitHub Secrets: SERVER_SSH_KEY${NC}"
echo ""
echo "5. 安全建议（项目部署完成后）："
echo -e "   ${CYAN}# 关闭密码登录，仅使用 Key 认证${NC}"
echo -e "   ${CYAN}# 编辑 /etc/ssh/sshd_config，设置 PasswordAuthentication no${NC}"
echo -e "   ${CYAN}# 然后运行：sudo systemctl restart ssh${NC}"
echo ""
echo "6. 查看 SSH 公钥（用于添加到 GitHub Actions）："
echo -e "   ${CYAN}cat ${SSH_DIR}/id_rsa.pub${NC}"
echo ""

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}重要信息：${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}•${NC} SSH 公钥位置：${SSH_DIR}/id_rsa.pub"
echo -e "  ${BLUE}•${NC} SSH 私钥位置：${SSH_DIR}/id_rsa（请妥善保管）"
echo -e "  ${BLUE}•${NC} Nginx 配置：${NGINX_CONFIG}"
echo -e "  ${BLUE}•${NC} 项目目录：${PROJECT_DIR}"
echo ""

success_msg "初始化脚本执行完成！"
