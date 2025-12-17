#!/bin/bash
# ============================================================
# 完整设置脚本：验证 + Nginx + HTTPS
# ============================================================
# 
# 一键完成所有配置步骤
# ============================================================

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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "完整设置：验证 + Nginx + HTTPS"
echo "========================================="
echo ""

# 步骤 1: 验证服务
step_msg "步骤 1/3: 验证服务运行状态"
echo ""
bash "$SCRIPT_DIR/verify-services.sh"
echo ""

# 询问是否继续
read -p "服务验证完成，是否继续配置 Nginx？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# 步骤 2: 配置 Nginx
step_msg "步骤 2/3: 配置 Nginx 反向代理"
echo ""
sudo bash "$SCRIPT_DIR/configure-nginx-proxy.sh"
echo ""

# 询问是否继续配置 HTTPS
read -p "Nginx 配置完成，是否配置 HTTPS？(y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    info_msg "跳过 HTTPS 配置"
    exit 0
fi

# 步骤 3: 配置 HTTPS
step_msg "步骤 3/3: 配置 HTTPS"
echo ""
sudo bash "$SCRIPT_DIR/configure-https-certbot.sh"
echo ""

# 完成
echo "========================================="
success_msg "所有配置完成！"
echo "========================================="
