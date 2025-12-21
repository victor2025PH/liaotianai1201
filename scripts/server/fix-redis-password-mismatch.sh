#!/bin/bash
# ============================================================
# 修复 Redis 密码大小写不匹配问题
# ============================================================

set -e

echo "=========================================="
echo "修复 Redis 密码不匹配问题"
echo "=========================================="
echo ""

REDIS_CONF="/etc/redis/redis.conf"

# 1. 检查当前 Redis 配置的密码
echo "[1] 检查当前 Redis 配置..."
echo "----------------------------------------"
if [ -f "$REDIS_CONF" ]; then
    CURRENT_PASSWORD=$(sudo grep "^requirepass" "$REDIS_CONF" | awk '{print $2}' | tr -d '"' | tr -d "'")
    if [ -n "$CURRENT_PASSWORD" ]; then
        echo "当前配置的密码: $CURRENT_PASSWORD"
        echo "密码长度: ${#CURRENT_PASSWORD}"
    else
        echo "⚠️  未找到 requirepass 配置"
    fi
else
    echo "❌ Redis 配置文件不存在: $REDIS_CONF"
    exit 1
fi
echo ""

# 2. 使用配置文件中实际存在的密码（统一使用）
echo "[2] 统一使用配置中的密码..."
echo "----------------------------------------"
if [ -z "$CURRENT_PASSWORD" ]; then
    echo "❌ 无法获取当前密码，使用默认密码"
    TARGET_PASSWORD="GTjd0yP2uQSnHeEHTA8CnnEbU"
else
    TARGET_PASSWORD="$CURRENT_PASSWORD"
fi

echo "将使用密码: $TARGET_PASSWORD"
echo ""

# 3. 确保 Redis 配置正确
echo "[3] 确保 Redis 配置正确..."
echo "----------------------------------------"
# 备份
sudo cp "$REDIS_CONF" "${REDIS_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# 确保密码正确设置
sudo sed -i "s/^# requirepass.*/requirepass $TARGET_PASSWORD/" "$REDIS_CONF"
sudo sed -i "s/^requirepass.*/requirepass $TARGET_PASSWORD/" "$REDIS_CONF"

# 确保 bind 配置正确
sudo sed -i 's/^# bind 127.0.0.1 ::1/bind 127.0.0.1 ::1/' "$REDIS_CONF"
if ! sudo grep -q "^bind 127.0.0.1 ::1" "$REDIS_CONF"; then
    # 如果不存在，添加它
    sudo sed -i '/^# bind 127.0.0.1 ::1/a bind 127.0.0.1 ::1' "$REDIS_CONF"
fi

echo "✅ Redis 配置已更新"
echo ""

# 4. 重启 Redis（关键步骤）
echo "[4] 重启 Redis 服务..."
echo "----------------------------------------"
sudo systemctl stop redis-server 2>/dev/null || true
sleep 2
sudo systemctl start redis-server
sleep 3

if sudo systemctl is-active --quiet redis-server; then
    echo "✅ Redis 服务运行中"
else
    echo "❌ Redis 服务未运行"
    sudo systemctl status redis-server --no-pager -l | head -15
    exit 1
fi
echo ""

# 5. 测试 Redis 连接（使用正确的密码）
echo "[5] 测试 Redis 连接..."
echo "----------------------------------------"
echo "使用密码: $TARGET_PASSWORD"
if redis-cli -a "$TARGET_PASSWORD" -h 127.0.0.1 PING 2>/dev/null | grep -q "PONG"; then
    echo "✅ Redis 连接成功！"
else
    echo "❌ Redis 连接失败，尝试详细测试..."
    redis-cli -a "$TARGET_PASSWORD" -h 127.0.0.1 PING
    echo ""
    echo "如果仍然失败，请检查："
    echo "  1. Redis 服务是否正常运行: sudo systemctl status redis-server"
    echo "  2. 配置文件中的密码: sudo grep requirepass $REDIS_CONF"
    exit 1
fi
echo ""

# 6. 创建 .env 文件（使用正确的密码）
echo "[6] 创建 .env 文件..."
echo "----------------------------------------"
cd ~/telegram-ai-system

# 在后端目录创建
if [ -d "admin-backend" ]; then
    mkdir -p admin-backend
    cat > admin-backend/.env << ENVEOF
# Redis 配置
REDIS_URL=redis://:$TARGET_PASSWORD@127.0.0.1:6379/0
REDIS_PASSWORD=$TARGET_PASSWORD
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
ENVEOF
    echo "✅ 已创建: admin-backend/.env"
    echo ""
    echo "文件内容："
    cat admin-backend/.env
    echo ""
fi

# 在项目根目录创建
cat > .env << ENVEOF
# Redis 配置
REDIS_URL=redis://:$TARGET_PASSWORD@127.0.0.1:6379/0
REDIS_PASSWORD=$TARGET_PASSWORD
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
ENVEOF
echo "✅ 已创建: .env"
echo ""
echo "文件内容："
cat .env
echo ""

# 7. 验证总结
echo "=========================================="
echo "✅ 修复完成"
echo "=========================================="
echo ""
echo "🔑 Redis 密码: $TARGET_PASSWORD"
echo ""
echo "📁 .env 文件位置:"
echo "  - admin-backend/.env"
echo "  - .env"
echo ""
echo "✅ Redis 连接测试: 成功"
echo ""
echo "下一步："
echo "  1. 重启后端服务以加载新的 Redis 密码"
echo "  2. 检查后端日志确认 Redis 连接成功"
echo ""
