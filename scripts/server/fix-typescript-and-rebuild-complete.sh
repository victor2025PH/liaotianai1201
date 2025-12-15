#!/bin/bash
# ============================================================
# 完整修复 TypeScript 错误、权限、构建和服务
# ============================================================

set -e

echo "=========================================="
echo "🔧 完整修复 TypeScript 错误并重新构建"
echo "=========================================="
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行: sudo bash $0"
    exit 1
fi

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"
TARGET_FILE="$FRONTEND_DIR/src/app/group-ai/groups/page.tsx"
FRONTEND_SERVICE="liaotian-frontend"

# 1. 修复权限
echo "[1/6] 修复权限..."
echo "----------------------------------------"
chown -R ubuntu:ubuntu "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
echo "✅ 权限已修复"
echo ""

# 2. 拉取最新代码
echo "[2/6] 拉取最新代码..."
echo "----------------------------------------"
cd "$PROJECT_DIR"
git pull origin main
echo "✅ 代码已更新"
echo ""

# 3. 修复 TypeScript 错误
echo "[3/6] 修复 TypeScript 错误..."
echo "----------------------------------------"
cd "$FRONTEND_DIR"

if [ ! -f "$TARGET_FILE" ]; then
    echo "❌ 文件不存在: $TARGET_FILE"
    exit 1
fi

# 使用 sed 进行简单修复（如果 Python 不可用）
# 修复 group.username.replace 调用，确保有防御性检查
if grep -q "const username = group.username.replace" "$TARGET_FILE"; then
    echo "发现需要修复的代码..."
    
    # 方法 1: 使用 sed 修复（简单可靠）
    # 确保在 replace 之前有 if 检查，并且使用安全的 replace
    sed -i 's/const username = group\.username\.replace/const username = (group.username || "").replace/g' "$TARGET_FILE"
    
    # 如果还没有 if 检查，添加一个
    if ! grep -A 2 "onClick={() => {" "$TARGET_FILE" | grep -q "if (!group.username)"; then
        # 在 onClick 回调开始后添加检查
        sed -i '/onClick={() => {/,/const username =/ {
            /const username =/ i\
                              if (!group.username) return
        }' "$TARGET_FILE"
    fi
    
    echo "✅ TypeScript 错误已修复（使用 sed）"
else
    echo "✅ 代码看起来已经修复"
fi

# 验证修复
if grep -q "(group.username || \"\")" "$TARGET_FILE" || grep -q "if (!group.username) return" "$TARGET_FILE"; then
    echo "✅ 修复验证通过"
else
    echo "⚠️  修复可能不完整，但继续执行..."
fi
echo ""

# 4. 清理并重新构建
echo "[4/6] 清理并重新构建前端..."
echo "----------------------------------------"
cd "$FRONTEND_DIR"

# 清理构建目录
if [ -d ".next" ]; then
    echo "清理 .next 目录..."
    rm -rf .next
fi

# 确保权限正确
chown -R ubuntu:ubuntu .

# 构建
echo "开始构建（这可能需要几分钟）..."
echo "----------------------------------------"
if npm run build 2>&1 | tee /tmp/frontend-build.log; then
    echo ""
    echo "✅ 构建成功"
else
    BUILD_EXIT_CODE=$?
    echo ""
    echo "❌ 构建失败 (退出码: $BUILD_EXIT_CODE)"
    echo ""
    echo "构建错误摘要:"
    grep -i "error\|failed\|Type error" /tmp/frontend-build.log | tail -20 || true
    echo ""
    echo "完整构建日志: /tmp/frontend-build.log"
    exit 1
fi

# 验证 standalone 目录
if [ ! -d ".next/standalone" ]; then
    echo "❌ standalone 目录不存在，构建可能不完整"
    echo "检查构建日志: /tmp/frontend-build.log"
    exit 1
fi

if [ ! -f ".next/standalone/server.js" ]; then
    echo "❌ standalone/server.js 不存在"
    exit 1
fi

echo "✅ standalone 构建验证通过"
echo ""

# 5. 修复服务配置并重启
echo "[5/6] 修复服务配置并重启..."
echo "----------------------------------------"
# 更新前端服务配置（使用绝对路径和工作目录）
cat > /etc/systemd/system/$FRONTEND_SERVICE.service <<EOF
[Unit]
Description=Liaotian Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=$FRONTEND_DIR/.next/standalone
Environment=NODE_ENV=production
Environment=PORT=3000
Environment=NODE_OPTIONS=--max-old-space-size=1024
ExecStart=/usr/bin/node $FRONTEND_DIR/.next/standalone/server.js
Restart=always
RestartSec=5
LimitNOFILE=65535

StandardOutput=journal
StandardError=journal
SyslogIdentifier=liaotian-frontend

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ 服务配置已更新"

# 重启前端服务
echo "重启前端服务..."
systemctl restart "$FRONTEND_SERVICE"
sleep 5

if systemctl is-active --quiet "$FRONTEND_SERVICE"; then
    echo "✅ 前端服务已启动"
    systemctl enable "$FRONTEND_SERVICE" 2>/dev/null || true
else
    echo "❌ 前端服务启动失败"
    echo ""
    echo "服务状态:"
    systemctl status "$FRONTEND_SERVICE" --no-pager -l | head -20
    echo ""
    echo "查看日志: sudo journalctl -u $FRONTEND_SERVICE -n 50 --no-pager"
    exit 1
fi

# 重启 Nginx
echo "重启 Nginx..."
if nginx -t 2>&1 | grep -q "successful"; then
    systemctl restart nginx
    if systemctl is-active --quiet nginx; then
        echo "✅ Nginx 已重启"
    else
        echo "⚠️  Nginx 重启失败"
        systemctl status nginx --no-pager -l | head -10
    fi
else
    echo "⚠️  Nginx 配置有错误，跳过重启"
    nginx -t
fi
echo ""

# 6. 验证 Nginx 配置
echo "[6/6] 验证 Nginx 配置..."
echo "----------------------------------------"
NGINX_CONFIG="/etc/nginx/sites-enabled/default"

# 检查是否有重复的 server 块
SERVER_BLOCKS=$(grep -c "^server {" "$NGINX_CONFIG" 2>/dev/null || echo "0")

if [ "$SERVER_BLOCKS" -gt 2 ]; then
    echo "⚠️  发现多个 server 块（可能有重复配置）"
    echo "Server 块数量: $SERVER_BLOCKS"
    echo ""
    echo "建议检查配置文件: $NGINX_CONFIG"
else
    echo "✅ Nginx 配置正常（$SERVER_BLOCKS 个 server 块）"
fi

# 测试 Nginx 配置语法
if nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置语法正确"
else
    echo "⚠️  Nginx 配置语法错误"
    nginx -t
fi
echo ""

# 最终验证
echo "=========================================="
echo "✅ 修复完成，开始验证..."
echo "=========================================="
echo ""

sleep 3

# 检查服务状态
echo "服务状态:"
BACKEND_STATUS=$(systemctl is-active "$FRONTEND_SERVICE" 2>/dev/null || echo "inactive")
echo "  前端 ($FRONTEND_SERVICE): $BACKEND_STATUS"
echo ""

# 检查端口
PORT_3000=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PORT_3000" ]; then
    echo "✅ 端口 3000 正在监听 (PID: $PORT_3000)"
else
    echo "❌ 端口 3000 未监听"
fi

# 测试服务
FRONTEND_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/login 2>/dev/null || echo "000")
if [ "$FRONTEND_TEST" = "200" ]; then
    echo "✅ 前端登录页面: HTTP 200"
else
    echo "⚠️  前端登录页面: HTTP $FRONTEND_TEST"
fi

# 测试 HTTPS
HTTPS_TEST=$(curl -s -o /dev/null -w "%{http_code}" https://aikz.usdt2026.cc/login 2>/dev/null || echo "000")
if [ "$HTTPS_TEST" = "200" ]; then
    echo "✅ HTTPS /login: HTTP 200"
else
    echo "⚠️  HTTPS /login: HTTP $HTTPS_TEST"
fi

echo ""
echo "=========================================="
echo "✅ 所有修复完成"
echo "=========================================="
echo ""
echo "如果仍有问题，请检查:"
echo "  构建日志: /tmp/frontend-build.log"
echo "  前端日志: sudo journalctl -u $FRONTEND_SERVICE -f"
echo "  Nginx 日志: sudo tail -f /var/log/nginx/error.log"
echo ""

