#!/bin/bash
# ============================================================
# 设置 Nginx 配置自动恢复机制
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
DOMAIN="aikz.usdt2026.cc"

echo "=========================================="
echo "🛡️  设置 Nginx 配置自动恢复机制"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "❌ 此脚本需要 sudo 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

# 1. 创建配置检查脚本
echo "[1/4] 创建配置检查脚本..."
echo "----------------------------------------"
cat > "$PROJECT_DIR/scripts/server/check-and-restore-nginx.sh" << 'CHECK_EOF'
#!/bin/bash
# 检查并自动恢复 Nginx HTTPS 配置

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"

# 检查是否有 HTTPS 配置
if [ -f "$NGINX_CONFIG" ]; then
    if ! grep -q "listen 443" "$NGINX_CONFIG"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 检测到 HTTPS 配置丢失，自动恢复..."
        /home/ubuntu/telegram-ai-system/scripts/server/ensure-https-config-persistent.sh >> /var/log/nginx-auto-restore.log 2>&1
    fi
fi
CHECK_EOF

chmod +x "$PROJECT_DIR/scripts/server/check-and-restore-nginx.sh"
chown ubuntu:ubuntu "$PROJECT_DIR/scripts/server/check-and-restore-nginx.sh"
echo "✅ 配置检查脚本已创建"
echo ""

# 2. 设置定时任务（每 5 分钟检查一次）
echo "[2/4] 设置定时检查任务..."
echo "----------------------------------------"
CRON_JOB="*/5 * * * * /home/ubuntu/telegram-ai-system/scripts/server/check-and-restore-nginx.sh"
(crontab -u ubuntu -l 2>/dev/null | grep -v "check-and-restore-nginx.sh"; echo "$CRON_JOB") | crontab -u ubuntu -
echo "✅ 定时检查任务已设置（每 5 分钟检查一次）"
echo ""

# 3. 设置 Certbot 后处理钩子
echo "[3/4] 设置 Certbot 后处理钩子..."
echo "----------------------------------------"
CERTBOT_DEPLOY_HOOK="/etc/letsencrypt/renewal-hooks/deploy/ensure-https.sh"
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy

cat > /tmp/certbot-deploy-hook.sh << 'HOOK_EOF'
#!/bin/bash
# Certbot 部署后自动恢复 HTTPS 配置

DOMAIN="aikz.usdt2026.cc"
NGINX_CONFIG="/etc/nginx/sites-available/${DOMAIN}"

# 等待 Certbot 完成
sleep 2

# 检查并恢复 HTTPS 配置
if [ -f "$NGINX_CONFIG" ] && ! grep -q "listen 443" "$NGINX_CONFIG"; then
    echo "[CERTBOT-HOOK] 检测到 HTTPS 配置丢失，自动恢复..."
    /home/ubuntu/telegram-ai-system/scripts/server/ensure-https-config-persistent.sh >> /var/log/certbot-hook.log 2>&1
    systemctl reload nginx
fi
HOOK_EOF

sudo mv /tmp/certbot-deploy-hook.sh "$CERTBOT_DEPLOY_HOOK"
sudo chmod +x "$CERTBOT_DEPLOY_HOOK"
echo "✅ Certbot 后处理钩子已设置"
echo ""

# 4. 创建 systemd 服务（在 Nginx 启动后检查配置）
echo "[4/4] 创建 systemd 服务..."
echo "----------------------------------------"
cat > /tmp/nginx-config-checker.service << 'SERVICE_EOF'
[Unit]
Description=Nginx HTTPS Config Checker
After=nginx.service
Requires=nginx.service

[Service]
Type=oneshot
ExecStart=/home/ubuntu/telegram-ai-system/scripts/server/check-and-restore-nginx.sh
RemainAfterExit=yes
User=root

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo mv /tmp/nginx-config-checker.service /etc/systemd/system/nginx-config-checker.service
sudo systemctl daemon-reload
sudo systemctl enable nginx-config-checker.service
echo "✅ systemd 服务已创建并启用"
echo ""

echo "=========================================="
echo "✅ 自动恢复机制设置完成"
echo "=========================================="
echo ""
echo "已实施的保护机制："
echo "  1. ✅ 定时检查（每 5 分钟）"
echo "  2. ✅ Certbot 后处理钩子"
echo "  3. ✅ systemd 服务（Nginx 启动后检查）"
echo ""
echo "查看日志："
echo "  tail -f /var/log/nginx-auto-restore.log"
echo "  tail -f /var/log/certbot-hook.log"
echo ""

