#!/bin/bash
# ============================================================
# 启动所有前后端服务
# ============================================================

set -e

PROJECT_DIR="/home/ubuntu/telegram-ai-system"

echo "=========================================="
echo "🚀 启动所有前后端服务"
echo "=========================================="
echo ""

# 检查是否以 root 或 sudo 运行
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "⚠️  某些操作需要 sudo 权限"
fi

# 1. 检查项目目录
echo "[1/5] 检查项目目录..."
echo "----------------------------------------"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    exit 1
fi
echo "✅ 项目目录存在"
cd "$PROJECT_DIR"
echo ""

# 2. 检查并启动 Redis
echo "[2/5] 检查并启动 Redis..."
echo "----------------------------------------"
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis 服务正在运行"
else
    echo "启动 Redis 服务..."
    sudo systemctl start redis-server
    sleep 2
    if systemctl is-active --quiet redis-server; then
        echo "✅ Redis 服务已启动"
    else
        echo "❌ Redis 服务启动失败"
        sudo systemctl status redis-server --no-pager | head -10
    fi
fi
echo ""

# 3. 检查 PM2 配置
echo "[3/5] 检查 PM2 配置..."
echo "----------------------------------------"
if [ -f "$PROJECT_DIR/ecosystem.config.js" ]; then
    echo "✅ ecosystem.config.js 存在"
else
    echo "❌ ecosystem.config.js 不存在"
    exit 1
fi
echo ""

# 4. 启动 PM2 服务
echo "[4/5] 启动 PM2 服务..."
echo "----------------------------------------"

# 检查 PM2 是否已安装
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 未安装"
    echo "   安装命令: sudo npm install -g pm2"
    exit 1
fi

# 检查当前 PM2 进程
PM2_LIST=$(sudo -u ubuntu pm2 list 2>/dev/null || echo "")

if echo "$PM2_LIST" | grep -q "backend.*online" && echo "$PM2_LIST" | grep -q "next-server.*online"; then
    echo "✅ 所有服务已在运行"
    echo ""
    echo "当前服务状态："
    sudo -u ubuntu pm2 list
else
    echo "启动服务..."
    
    # 停止所有旧进程（如果有）
    sudo -u ubuntu pm2 stop all 2>/dev/null || true
    sudo -u ubuntu pm2 delete all 2>/dev/null || true
    
    # 启动所有服务
    sudo -u ubuntu bash -c "cd $PROJECT_DIR && pm2 start ecosystem.config.js"
    
    # 保存 PM2 配置
    sudo -u ubuntu pm2 save
    
    echo "⏳ 等待服务初始化..."
    sleep 5
    
    echo ""
    echo "服务状态："
    sudo -u ubuntu pm2 list
fi
echo ""

# 5. 验证服务状态
echo "[5/5] 验证服务状态..."
echo "----------------------------------------"

# 检查端口监听
echo "检查端口监听："
if sudo ss -tlnp | grep -q ":8000 "; then
    echo "✅ 端口 8000 (后端) 正在监听"
else
    echo "❌ 端口 8000 (后端) 未监听"
fi

if sudo ss -tlnp | grep -q ":3000 "; then
    echo "✅ 端口 3000 (前端) 正在监听"
else
    echo "❌ 端口 3000 (前端) 未监听"
fi
echo ""

# 测试服务健康检查
echo "测试服务健康检查："
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo "✅ 后端健康检查通过"
else
    echo "⚠️  后端健康检查失败 (状态码: $BACKEND_HEALTH)"
fi

FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000 || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "301" ] || [ "$FRONTEND_HEALTH" = "302" ]; then
    echo "✅ 前端服务响应正常"
else
    echo "⚠️  前端服务响应异常 (状态码: $FRONTEND_HEALTH)"
fi
echo ""

# 6. 检查 Nginx
echo "检查 Nginx 状态..."
echo "----------------------------------------"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务正在运行"
else
    echo "⚠️  Nginx 服务未运行"
    echo "   启动命令: sudo systemctl start nginx"
fi
echo ""

echo "=========================================="
echo "✅ 服务启动完成"
echo "=========================================="
echo ""
echo "查看服务状态："
echo "  sudo -u ubuntu pm2 list"
echo "  sudo -u ubuntu pm2 logs"
echo "  sudo -u ubuntu pm2 monit"
echo ""
echo "查看服务日志："
echo "  sudo -u ubuntu pm2 logs backend"
echo "  sudo -u ubuntu pm2 logs next-server"
echo ""
