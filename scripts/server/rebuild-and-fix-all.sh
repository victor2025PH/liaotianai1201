#!/bin/bash
# ============================================================
# 重新构建前端并修复所有问题
# ============================================================

echo "=========================================="
echo "🔧 重新构建前端并修复所有问题"
echo "=========================================="
echo ""

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
FRONTEND_DIR="$PROJECT_DIR/saas-demo"

# 1. 停止所有服务
echo "[1/6] 停止所有服务..."
echo "----------------------------------------"
sudo -u ubuntu pm2 stop all 2>/dev/null || true
sudo -u deployer pm2 stop all 2>/dev/null || true
sleep 2
echo "✅ 所有服务已停止"
echo ""

# 2. 清理端口
echo "[2/6] 清理端口..."
echo "----------------------------------------"
sudo lsof -t -i:3000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sudo lsof -t -i:8000 2>/dev/null | xargs sudo kill -9 2>/dev/null || true
sudo pkill -9 -f "next-server" 2>/dev/null || true
sleep 3
echo "✅ 端口已清理"
echo ""

# 3. 检查并启用 Swap
echo "[3/6] 检查并启用 Swap..."
echo "----------------------------------------"
if [ ! -f /swapfile ]; then
    echo "创建 2GB Swap 文件..."
    sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap 已创建"
else
    sudo swapon /swapfile 2>/dev/null || true
    echo "✅ Swap 已启用"
fi
free -h
echo ""

# 4. 重新构建前端
echo "[4/6] 重新构建前端（这可能需要几分钟）..."
echo "----------------------------------------"
cd "$FRONTEND_DIR" || exit 1

# 清理旧的构建
echo "清理旧的构建..."
rm -rf .next
rm -f .next/lock

# 安装依赖
echo "安装依赖..."
export NODE_OPTIONS="--max-old-space-size=1536"
npm install --prefer-offline --no-audit

# 构建
echo "开始构建..."
npm run build

# 验证构建结果
if [ ! -d ".next/standalone" ]; then
    echo "❌ 构建失败：standalone 目录不存在"
    exit 1
fi

echo "✅ 构建完成"
echo ""

# 5. 处理静态资源
echo "[5/6] 处理静态资源..."
echo "----------------------------------------"
STANDALONE_DIR=".next/standalone"
if [ -d ".next/standalone/saas-demo" ]; then
    STANDALONE_DIR=".next/standalone/saas-demo"
fi

# 确保目录存在
mkdir -p "$STANDALONE_DIR/.next/static"
mkdir -p "$STANDALONE_DIR/.next/server"
mkdir -p "$STANDALONE_DIR/.next"

# 复制 BUILD_ID
if [ -f ".next/BUILD_ID" ]; then
    cp .next/BUILD_ID "$STANDALONE_DIR/.next/BUILD_ID" 2>/dev/null || true
fi

# 复制所有 JSON 文件
for json_file in .next/*.json; do
    if [ -f "$json_file" ]; then
        cp "$json_file" "$STANDALONE_DIR/.next/" 2>/dev/null || true
    fi
done

# 复制 static 目录
if [ -d ".next/static" ]; then
    cp -r .next/static/* "$STANDALONE_DIR/.next/static/" 2>/dev/null || true
fi

# 复制 server 目录
if [ -d ".next/server" ]; then
    cp -r .next/server/* "$STANDALONE_DIR/.next/server/" 2>/dev/null || true
fi

# 复制 public 目录
if [ -d "public" ]; then
    cp -r public "$STANDALONE_DIR/" 2>/dev/null || true
fi

echo "✅ 静态资源处理完成"
echo ""

# 6. 启动服务并检查 Nginx
echo "[6/6] 启动服务并检查 Nginx..."
echo "----------------------------------------"
cd "$PROJECT_DIR" || exit 1

# 启动 PM2 服务
sudo -u ubuntu pm2 start ecosystem.config.js
sleep 5

# 检查服务状态
echo "PM2 服务状态:"
sudo -u ubuntu pm2 list

# 检查端口
echo ""
echo "端口监听状态:"
sudo ss -tlnp | grep -E ":(3000|8000) " || echo "端口未监听"

# 检查 Nginx
echo ""
echo "检查 Nginx 状态..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 正在运行"
    
    # 测试 Nginx 配置
    if sudo nginx -t 2>/dev/null; then
        echo "✅ Nginx 配置正确"
        sudo systemctl reload nginx
    else
        echo "⚠️  Nginx 配置有错误"
        sudo nginx -t
    fi
else
    echo "❌ Nginx 未运行，正在启动..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
fi

# 保存 PM2 配置
sudo -u ubuntu pm2 save

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "服务状态："
sudo -u ubuntu pm2 list
echo ""
echo "Nginx 状态："
sudo systemctl status nginx --no-pager | head -5
echo ""
echo "如果网站仍无法访问，请检查："
echo "1. Nginx 配置: sudo nginx -t"
echo "2. 防火墙设置: sudo ufw status"
echo "3. 服务日志: sudo -u ubuntu pm2 logs frontend --lines 50"

