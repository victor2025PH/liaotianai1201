#!/bin/bash
# ============================================================
# 完整安全配置脚本
# ============================================================

set -e

echo "=========================================="
echo "🔒 完整安全配置"
echo "=========================================="
echo ""

# 1. 配置防火墙
echo "[1/6] 配置防火墙..."
if command -v ufw >/dev/null 2>&1; then
    echo "  启用防火墙..."
    sudo ufw --force enable || true
    
    echo "  设置默认策略..."
    sudo ufw default deny incoming || true
    sudo ufw default allow outgoing || true
    
    echo "  允许 SSH..."
    sudo ufw allow ssh || true
    
    echo "  允许 HTTP/HTTPS..."
    sudo ufw allow 80/tcp || true
    sudo ufw allow 443/tcp || true
    
    echo "  防火墙状态:"
    sudo ufw status | head -10
else
    echo "  ⚠️  UFW 未安装，跳过防火墙配置"
fi
echo ""

# 2. 安装 fail2ban
echo "[2/6] 安装 fail2ban..."
if ! command -v fail2ban-client >/dev/null 2>&1; then
    echo "  正在安装 fail2ban..."
    sudo apt-get update -qq
    sudo apt-get install -y fail2ban || {
        echo "  ⚠️  fail2ban 安装失败，请手动安装"
    }
else
    echo "  ✅ fail2ban 已安装"
fi

if command -v fail2ban-client >/dev/null 2>&1; then
    echo "  启动 fail2ban..."
    sudo systemctl enable fail2ban || true
    sudo systemctl start fail2ban || true
    
    echo "  fail2ban 状态:"
    sudo fail2ban-client status 2>/dev/null | head -5 || echo "    服务未运行"
fi
echo ""

# 3. 配置 SSH 安全
echo "[3/6] 配置 SSH 安全..."
SSH_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSH_CONFIG" ]; then
    echo "  当前 SSH 配置:"
    echo "    PermitRootLogin: $(grep -E "^PermitRootLogin" "$SSH_CONFIG" || echo "PermitRootLogin yes (默认)")"
    echo "    PasswordAuthentication: $(grep -E "^PasswordAuthentication" "$SSH_CONFIG" || echo "PasswordAuthentication yes (默认)")"
    echo "    PubkeyAuthentication: $(grep -E "^PubkeyAuthentication" "$SSH_CONFIG" || echo "PubkeyAuthentication yes (默认)")"
    echo ""
    echo "  建议配置（需要手动编辑）:"
    echo "    sudo nano $SSH_CONFIG"
    echo "    设置: PermitRootLogin no"
    echo "    设置: PasswordAuthentication no (如果使用密钥认证)"
    echo "    设置: PubkeyAuthentication yes"
    echo "    然后: sudo systemctl restart sshd"
else
    echo "  ⚠️  SSH 配置文件不存在"
fi
echo ""

# 4. 安装安全工具
echo "[4/6] 安装安全工具..."
SECURITY_TOOLS=("rkhunter" "chkrootkit" "debsums")

for tool in "${SECURITY_TOOLS[@]}"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "  安装 $tool..."
        sudo apt-get install -y "$tool" || echo "    ⚠️  $tool 安装失败"
    else
        echo "  ✅ $tool 已安装"
    fi
done
echo ""

# 5. 配置自动更新
echo "[5/6] 配置自动更新..."
if command -v unattended-upgrades >/dev/null 2>&1; then
    echo "  ✅ unattended-upgrades 已安装"
    echo "  配置自动更新:"
    echo "    sudo dpkg-reconfigure -plow unattended-upgrades"
else
    echo "  安装 unattended-upgrades..."
    sudo apt-get install -y unattended-upgrades || echo "    ⚠️  安装失败"
fi
echo ""

# 6. 创建安全监控脚本
echo "[6/6] 创建安全监控脚本..."
MONITOR_SCRIPT="/usr/local/bin/security-monitor.sh"
sudo tee "$MONITOR_SCRIPT" > /dev/null << 'EOF'
#!/bin/bash
# 安全监控脚本
LOG_FILE="/var/log/security-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 安全监控检查" >> "$LOG_FILE"

# 检查可疑进程
SUSPICIOUS=$(ps aux | grep -iE "miner|crypto|bitcoin|monero|80.64.16.241" | grep -v grep || true)
if [ -n "$SUSPICIOUS" ]; then
    echo "[$DATE] ⚠️  发现可疑进程" >> "$LOG_FILE"
    echo "$SUSPICIOUS" >> "$LOG_FILE"
fi

# 检查可疑文件
if [ -f "/data/MUTA71VL" ] || [ -f "/data/CX81yM9aE" ]; then
    echo "[$DATE] ⚠️  发现可疑文件" >> "$LOG_FILE"
fi

# 检查恶意定时任务
if crontab -l 2>/dev/null | grep -q "80.64.16.241\|unk.sh"; then
    echo "[$DATE] ⚠️  发现恶意定时任务" >> "$LOG_FILE"
fi

# 检查系统资源
CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
MEM=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')

if (( $(echo "$CPU > 90" | bc -l) )); then
    echo "[$DATE] ⚠️  CPU 使用率过高: ${CPU}%" >> "$LOG_FILE"
fi

if [ "$MEM" -gt 90 ]; then
    echo "[$DATE] ⚠️  内存使用率过高: ${MEM}%" >> "$LOG_FILE"
fi
EOF

sudo chmod +x "$MONITOR_SCRIPT"
echo "  ✅ 监控脚本已创建: $MONITOR_SCRIPT"
echo "  添加到定时任务（每天凌晨 2 点运行）:"
echo "    0 2 * * * $MONITOR_SCRIPT"
echo ""

# 总结
echo "=========================================="
echo "安全配置完成"
echo "=========================================="
echo ""
echo "已完成的配置:"
echo "  ✅ 防火墙配置"
echo "  ✅ fail2ban 安装和配置"
echo "  ✅ 安全工具安装"
echo "  ✅ 安全监控脚本创建"
echo ""
echo "需要手动完成的配置:"
echo "  1. SSH 安全配置（编辑 /etc/ssh/sshd_config）"
echo "  2. 配置自动更新（sudo dpkg-reconfigure unattended-upgrades）"
echo "  3. 添加安全监控到定时任务"
echo "  4. 更改所有密码"
echo ""

