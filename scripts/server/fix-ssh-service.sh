#!/bin/bash
# ============================================================
# 修复 SSH 服务重启问题
# ============================================================
# 
# 说明：
# 在 Ubuntu 22.04 中，SSH 服务的正确名称是 ssh.service
# 而不是 sshd.service
# 
# 使用方法：
#   sudo bash scripts/server/fix-ssh-service.sh
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

if [ "$EUID" -ne 0 ]; then 
    error_msg "请使用 sudo 运行此脚本"
    exit 1
fi

echo "正在修复 SSH 服务..."

# 检查 SSH 配置文件是否存在
SSH_CONFIG="/etc/ssh/sshd_config"
if [ ! -f "$SSH_CONFIG" ]; then
    error_msg "SSH 配置文件不存在: $SSH_CONFIG"
    exit 1
fi

# 确保 SSH 配置已优化
info_msg "检查 SSH 配置..."

if ! grep -q "^ClientAliveInterval 60" "$SSH_CONFIG"; then
    echo "ClientAliveInterval 60" >> "$SSH_CONFIG"
    info_msg "已添加 ClientAliveInterval 60"
fi

if ! grep -q "^ClientAliveCountMax 3" "$SSH_CONFIG"; then
    echo "ClientAliveCountMax 3" >> "$SSH_CONFIG"
    info_msg "已添加 ClientAliveCountMax 3"
fi

# 尝试重启 SSH 服务
info_msg "重启 SSH 服务..."

if systemctl is-active --quiet ssh 2>/dev/null; then
    systemctl restart ssh
    success_msg "SSH 服务重启成功（使用 ssh.service）"
elif systemctl is-active --quiet sshd 2>/dev/null; then
    systemctl restart sshd
    success_msg "SSH 服务重启成功（使用 sshd.service）"
else
    error_msg "无法找到 SSH 服务"
    info_msg "请手动检查: systemctl status ssh 或 systemctl status sshd"
    exit 1
fi

# 验证服务状态
sleep 2
if systemctl is-active --quiet ssh 2>/dev/null || systemctl is-active --quiet sshd 2>/dev/null; then
    success_msg "SSH 服务运行正常"
    
    echo ""
    info_msg "当前 SSH 配置："
    echo "  ClientAliveInterval: $(grep "^ClientAliveInterval" "$SSH_CONFIG" | tail -1 || echo '未设置')"
    echo "  ClientAliveCountMax: $(grep "^ClientAliveCountMax" "$SSH_CONFIG" | tail -1 || echo '未设置')"
    echo "  PasswordAuthentication: $(grep "^PasswordAuthentication" "$SSH_CONFIG" | tail -1 || echo '未设置')"
    echo "  PubkeyAuthentication: $(grep "^PubkeyAuthentication" "$SSH_CONFIG" | tail -1 || echo '未设置')"
else
    error_msg "SSH 服务未运行，请检查系统日志"
    exit 1
fi

echo ""
success_msg "SSH 服务修复完成！"
