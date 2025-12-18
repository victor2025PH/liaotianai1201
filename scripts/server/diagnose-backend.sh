#!/bin/bash
# 后端服务诊断和修复脚本
# 使用方法: bash scripts/server/diagnose-backend.sh

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
USER="ubuntu"

echo "=========================================="
echo "后端服务诊断和修复脚本"
echo "=========================================="
echo ""

# 1. 查看错误日志
echo "1️⃣ 查看后端错误日志..."
echo "----------------------------------------"
sudo -u $USER pm2 logs backend --lines 50 --nostream 2>&1 || echo "⚠️  无法获取日志（服务可能未启动）"
echo ""

# 2. 检查并修复配置文件 (.env)
echo "2️⃣ 检查并修复配置文件..."
echo "----------------------------------------"
cd "$BACKEND_DIR" || exit 1

if [ ! -f .env ]; then
    echo "⚠️  缺少 .env 文件，正在从 env.example 复制..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ 已从 env.example 创建 .env 文件"
        echo "⚠️  注意：请确保 .env 文件中的配置（如 JWT_SECRET、CORS_ORIGINS）适合生产环境"
    else
        echo "❌ 错误：env.example 文件不存在，无法创建 .env"
        echo "   将创建一个基本的 .env 文件..."
        cat > .env << 'ENVEOF'
JWT_SECRET=change_me_production_key_please_change
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_DEFAULT_EMAIL=admin@example.com
ADMIN_DEFAULT_PASSWORD=changeme123
CORS_ORIGINS=http://localhost:3000,https://aikz.usdt2026.cc
DATABASE_URL=sqlite:///./admin.db
ENVEOF
        echo "✅ 已创建基本的 .env 文件"
    fi
else
    echo "✅ .env 文件已存在"
    echo "📄 .env 文件内容预览（隐藏敏感信息）:"
    grep -E "^[^=]*=" .env | sed 's/=.*/=***/' | head -10
fi
echo ""

# 3. 重启后端
echo "3️⃣ 重启后端服务..."
echo "----------------------------------------"
sudo -u $USER pm2 restart backend || {
    echo "⚠️  PM2 restart 失败，尝试重新启动..."
    sudo -u $USER pm2 delete backend 2>/dev/null || true
    cd "$PROJECT_DIR"
    sudo -u $USER pm2 start ecosystem.config.js --only backend
}
sudo -u $USER pm2 save
echo "⏳ 等待服务启动 (5秒)..."
sleep 5
echo ""

# 4. 验证端口
echo "4️⃣ 验证端口 8000 是否正在监听..."
echo "----------------------------------------"
if command -v netstat &> /dev/null; then
    sudo netstat -tulpn | grep 8000 || echo "❌ 端口 8000 未被监听"
elif command -v ss &> /dev/null; then
    sudo ss -tulpn | grep 8000 || echo "❌ 端口 8000 未被监听"
else
    echo "⚠️  未找到 netstat 或 ss 命令，使用 lsof 检查..."
    sudo lsof -i:8000 || echo "❌ 端口 8000 未被监听"
fi
echo ""

# 5. 检查服务状态
echo "5️⃣ 检查 PM2 服务状态..."
echo "----------------------------------------"
sudo -u $USER pm2 list
echo ""

# 6. 最终检查
echo "6️⃣ 最终检查 - 后端日志（最后 20 行）..."
echo "----------------------------------------"
sudo -u $USER pm2 logs backend --lines 20 --nostream 2>&1 || echo "⚠️  无法获取日志"
echo ""

echo "=========================================="
echo "诊断完成！"
echo "=========================================="
