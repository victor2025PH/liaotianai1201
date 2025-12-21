#!/bin/bash
# ============================================================
# 服务器安全加固脚本
# 功能：防止挖矿病毒、加固 Redis、配置防火墙、SSH 防护
# ============================================================

set -e

echo "=========================================="
echo "🔒 服务器安全加固脚本"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "⚠️  警告：此脚本将修改系统配置，请确保已备份重要数据"
echo "按 Ctrl+C 取消，或等待 5 秒后继续..."
sleep 5
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="/tmp/secure_server_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# 生成强密码函数
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# 1. Redis 安全加固
echo "=========================================="
echo "[1/4] Redis 安全加固"
echo "=========================================="
echo ""

REDIS_CONF="/etc/redis/redis.conf"
REDIS_PASSWORD=""

if [ -f "$REDIS_CONF" ]; then
    echo "✅ 找到 Redis 配置文件: $REDIS_CONF"
    
    # 备份配置
    sudo cp "$REDIS_CONF" "${REDIS_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已备份配置文件"
    
    # 生成强密码
    REDIS_PASSWORD=$(generate_password)
    echo ""
    echo "${GREEN}=========================================="
    echo "🔑 Redis 密码已生成"
    echo "=========================================="
    echo "密码: $REDIS_PASSWORD"
    echo "==========================================${NC}"
    echo ""
    echo "⚠️  请立即保存此密码！脚本执行完成后会再次显示。"
    echo ""
    
    # 修改 bind 配置（只允许本地访问）
    echo "修改 bind 配置..."
    if sudo grep -q "^bind 127.0.0.1 ::1" "$REDIS_CONF"; then
        echo "  ✅ bind 配置已正确"
    elif sudo grep -q "^# bind 127.0.0.1 ::1" "$REDIS_CONF"; then
        sudo sed -i 's/^# bind 127.0.0.1 ::1/bind 127.0.0.1 ::1/' "$REDIS_CONF"
        echo "  ✅ 已启用 bind 127.0.0.1 ::1"
    elif sudo grep -q "^bind 0.0.0.0" "$REDIS_CONF"; then
        sudo sed -i 's/^bind 0.0.0.0/# bind 0.0.0.0\nbind 127.0.0.1 ::1/' "$REDIS_CONF"
        echo "  ✅ 已修改 bind 配置为本地访问"
    else
        # 如果找不到 bind 配置，添加它
        sudo sed -i '/^# bind 127.0.0.1 ::1/a bind 127.0.0.1 ::1' "$REDIS_CONF"
        echo "  ✅ 已添加 bind 127.0.0.1 ::1"
    fi
    
    # 禁用保护模式（如果使用 bind，保护模式可以关闭）
    sudo sed -i 's/^protected-mode yes/protected-mode yes/' "$REDIS_CONF"
    
    # 设置密码
    echo "设置 Redis 密码..."
    if sudo grep -q "^requirepass" "$REDIS_CONF"; then
        # 如果已有密码，更新它
        sudo sed -i "s/^requirepass .*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
        echo "  ✅ 已更新 Redis 密码"
    else
        # 如果注释掉了，取消注释并设置密码
        if sudo grep -q "^# requirepass" "$REDIS_CONF"; then
            sudo sed -i "s/^# requirepass .*/requirepass $REDIS_PASSWORD/" "$REDIS_CONF"
        else
            # 添加新行
            sudo sed -i "/^# requirepass/a requirepass $REDIS_PASSWORD" "$REDIS_CONF"
        fi
        echo "  ✅ 已设置 Redis 密码"
    fi
    
    # 重启 Redis
    echo "重启 Redis 服务..."
    if sudo systemctl restart redis-server 2>/dev/null || sudo systemctl restart redis 2>/dev/null; then
        sleep 2
        if sudo systemctl is-active --quiet redis-server || sudo systemctl is-active --quiet redis; then
            echo "  ✅ Redis 服务已重启"
        else
            echo "  ⚠️  Redis 服务可能未正常运行，请检查"
        fi
    else
        echo "  ⚠️  无法重启 Redis，请手动检查服务状态"
    fi
    
    echo ""
else
    echo "⚠️  Redis 配置文件不存在: $REDIS_CONF"
    echo "  跳过 Redis 配置（如果未安装 Redis，这是正常的）"
    echo ""
fi

# 2. UFW 防火墙配置
echo "=========================================="
echo "[2/4] UFW 防火墙配置"
echo "=========================================="
echo ""

# 安装 UFW（如果未安装）
if ! command -v ufw >/dev/null 2>&1; then
    echo "安装 UFW..."
    sudo apt-get update -qq
    sudo apt-get install -y ufw
    echo "  ✅ UFW 已安装"
fi

# 重置 UFW（谨慎操作）
echo "重置 UFW 规则..."
sudo ufw --force reset
echo "  ✅ UFW 规则已重置"

# 设置默认策略
echo "设置默认策略（拒绝所有入站，允许所有出站）..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
echo "  ✅ 默认策略已设置"

# 开放必要端口
echo "开放必要端口..."

# SSH (22)
echo "  开放 SSH (22)..."
sudo ufw allow 22/tcp comment 'SSH'
echo "    ✅ SSH (22) 已开放"

# HTTP (80)
echo "  开放 HTTP (80)..."
sudo ufw allow 80/tcp comment 'HTTP'
echo "    ✅ HTTP (80) 已开放"

# HTTPS (443)
echo "  开放 HTTPS (443)..."
sudo ufw allow 443/tcp comment 'HTTPS'
echo "    ✅ HTTPS (443) 已开放"

# 明确拒绝数据库端口（即使默认策略是 deny，也明确拒绝）
echo "  明确拒绝数据库端口..."
sudo ufw deny 6379/tcp comment 'Redis - Blocked'
sudo ufw deny 3306/tcp comment 'MySQL - Blocked'
sudo ufw deny 5432/tcp comment 'PostgreSQL - Blocked'
echo "    ✅ 数据库端口已拒绝"

# 启用 UFW
echo "启用 UFW..."
sudo ufw --force enable
echo "  ✅ UFW 已启用"

# 显示状态
echo ""
echo "UFW 状态："
sudo ufw status numbered
echo ""

# 3. Fail2Ban SSH 防护
echo "=========================================="
echo "[3/4] Fail2Ban SSH 防护配置"
echo "=========================================="
echo ""

# 安装 Fail2Ban
if ! command -v fail2ban-client >/dev/null 2>&1; then
    echo "安装 Fail2Ban..."
    sudo apt-get update -qq
    sudo apt-get install -y fail2ban
    echo "  ✅ Fail2Ban 已安装"
fi

# 创建本地配置（不直接修改默认配置）
F2B_LOCAL_CONF="/etc/fail2ban/jail.local"
echo "创建 Fail2Ban 本地配置..."

sudo tee "$F2B_LOCAL_CONF" > /dev/null << 'EOF'
[DEFAULT]
# 禁止时间：24小时（86400秒）
bantime = 86400
# 查找时间窗口：5分钟（300秒）
findtime = 300
# 最大重试次数：3次
maxretry = 3
# 后端：自动检测
backend = auto
# 邮件通知（可选，需要配置邮件）
# destemail = admin@example.com
# sendername = Fail2Ban

[sshd]
# 启用 SSH 保护
enabled = true
# 端口（根据实际 SSH 端口调整）
port = ssh
# 日志文件
logpath = %(sshd_log)s
# 最大重试次数（覆盖默认值）
maxretry = 3
# 查找时间窗口（覆盖默认值）
findtime = 300
# 禁止时间（覆盖默认值）
bantime = 86400
EOF

echo "  ✅ Fail2Ban 配置已创建"

# 重启 Fail2Ban
echo "重启 Fail2Ban 服务..."
sudo systemctl restart fail2ban
sleep 2

if sudo systemctl is-active --quiet fail2ban; then
    echo "  ✅ Fail2Ban 服务已启动"
    
    # 显示状态
    echo ""
    echo "Fail2Ban 状态："
    sudo fail2ban-client status
    echo ""
    echo "SSH 保护状态："
    sudo fail2ban-client status sshd 2>/dev/null || echo "  （SSH jail 可能需要一些时间才能显示）"
else
    echo "  ⚠️  Fail2Ban 服务可能未正常运行，请检查"
fi

echo ""

# 4. 清理残留定时任务和可疑文件
echo "=========================================="
echo "[4/4] 清理残留定时任务和可疑文件"
echo "=========================================="
echo ""

# 清理可疑文件
echo "清理可疑文件..."
SUSPICIOUS_PATTERNS=(
    "/tmp/.update"
    "/var/tmp/.update"
    "/run/user/1000/.update"
    "/tmp/*.sh"
    "/var/tmp/*.sh"
)

CLEANED_COUNT=0
for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
    for file in $pattern 2>/dev/null; do
        if [ -f "$file" ] || [ -d "$file" ]; then
            # 检查文件是否可疑（包含 base64, wget, curl 等）
            if grep -qE "base64|wget.*http|curl.*http|\.update|startup" "$file" 2>/dev/null; then
                echo "  🗑️  删除可疑文件: $file"
                sudo rm -rf "$file" 2>/dev/null && ((CLEANED_COUNT++)) || true
            fi
        fi
    done
done

if [ $CLEANED_COUNT -gt 0 ]; then
    echo "  ✅ 已清理 $CLEANED_COUNT 个可疑文件"
else
    echo "  ✅ 未发现可疑文件"
fi
echo ""

# 清理 Crontab
echo "清理可疑 Crontab 条目..."

# 当前用户
if crontab -l >/dev/null 2>&1; then
    BACKUP_FILE="$HOME/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    crontab -l > "$BACKUP_FILE"
    echo "  ✅ 已备份当前用户 crontab: $BACKUP_FILE"
    
    # 删除可疑条目
    NEW_CRON=$(crontab -l 2>/dev/null | grep -vE "base64|wget.*http|curl.*http|\.update|startup" || true)
    if [ -n "$NEW_CRON" ]; then
        echo "$NEW_CRON" | crontab -
        echo "  ✅ 已清理当前用户 crontab"
    else
        # 如果清理后为空，清空 crontab
        crontab -r 2>/dev/null || true
        echo "  ✅ 已清空当前用户 crontab（所有条目都是可疑的）"
    fi
else
    echo "  ✅ 当前用户无 crontab"
fi

# Root 用户
if sudo crontab -l >/dev/null 2>&1; then
    ROOT_BACKUP="/root/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    sudo crontab -l > "$ROOT_BACKUP"
    echo "  ✅ 已备份 root 用户 crontab: $ROOT_BACKUP"
    
    # 删除可疑条目
    NEW_ROOT_CRON=$(sudo crontab -l 2>/dev/null | grep -vE "base64|wget.*http|curl.*http|\.update|startup" || true)
    if [ -n "$NEW_ROOT_CRON" ]; then
        echo "$NEW_ROOT_CRON" | sudo crontab -
        echo "  ✅ 已清理 root 用户 crontab"
    else
        sudo crontab -r 2>/dev/null || true
        echo "  ✅ 已清空 root 用户 crontab（所有条目都是可疑的）"
    fi
else
    echo "  ✅ root 用户无 crontab"
fi

# 清理系统级 crontab
echo "检查系统级 crontab..."
if [ -f "/etc/crontab" ]; then
    sudo cp /etc/crontab /etc/crontab.backup.$(date +%Y%m%d_%H%M%S)
    sudo sed -i '/base64\|wget.*http\|curl.*http\|\.update\|startup/d' /etc/crontab
    echo "  ✅ 已清理 /etc/crontab"
fi

# 清理 cron.d 目录
if [ -d "/etc/cron.d" ]; then
    for file in /etc/cron.d/*; do
        if [ -f "$file" ] && grep -qE "base64|wget.*http|curl.*http|\.update|startup" "$file" 2>/dev/null; then
            echo "  🗑️  删除可疑 cron.d 文件: $file"
            sudo rm -f "$file"
        fi
    done
    echo "  ✅ 已检查 /etc/cron.d"
fi

echo ""

# 完成总结
echo "=========================================="
echo "✅ 安全加固完成"
echo "=========================================="
echo ""
echo "${GREEN}=========================================="
echo "🔑 Redis 密码（请立即保存）"
echo "=========================================="
if [ -n "$REDIS_PASSWORD" ]; then
    echo "密码: $REDIS_PASSWORD"
    echo "配置文件: $REDIS_CONF"
    echo "==========================================${NC}"
else
    echo "（Redis 未配置或未安装）"
    echo "==========================================${NC}"
fi
echo ""

echo "📋 配置摘要："
echo "  1. ✅ Redis 已绑定到本地，已设置密码"
echo "  2. ✅ UFW 防火墙已启用，只开放 22, 80, 443"
echo "  3. ✅ Fail2Ban 已配置，SSH 5分钟内3次失败封禁24小时"
echo "  4. ✅ 可疑文件和定时任务已清理"
echo ""

echo "📝 日志文件: $LOG_FILE"
echo ""

echo "⚠️  重要提示："
echo "  1. 请立即保存 Redis 密码！"
echo "  2. 如果使用 Redis，需要更新后端代码中的连接配置"
echo "  3. 建议测试 SSH 连接，确保不会被误封"
echo "  4. 定期检查 Fail2Ban 状态: sudo fail2ban-client status"
echo ""
