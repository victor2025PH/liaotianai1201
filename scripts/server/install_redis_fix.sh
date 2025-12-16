#!/bin/bash
# ============================================================
# Redis 安装和配置脚本
# ============================================================
# 
# 功能：
# 1. 安装 Redis 服务
# 2. 配置 Redis（启用 systemd 监督）
# 3. 启动并启用 Redis
# 4. 验证安装
# 5. 重启后端服务
#
# 使用方法：sudo bash scripts/server/install_redis_fix.sh
# ============================================================

set -e  # 遇到错误立即退出

echo "============================================================"
echo "Redis 安装和配置脚本"
echo "============================================================"
echo "开始时间: $(date)"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "❌ 此脚本需要 root 权限，请使用 sudo 运行"
    echo "   使用方法: sudo bash scripts/server/install_redis_fix.sh"
    exit 1
fi

# ============================================================
# [1/4] 安装 Redis
# ============================================================
echo "[1/4] 安装 Redis 服务"
echo "------------------------------------------------------------"

# 检查 Redis 是否已安装
if command -v redis-cli > /dev/null 2>&1 && command -v redis-server > /dev/null 2>&1; then
    echo "✅ Redis 已安装"
    redis-cli --version
    redis-server --version
    echo ""
    echo "⚠️  检测到 Redis 已安装，将跳过安装步骤，继续配置..."
    echo ""
else
    echo "□ 更新 apt 源..."
    apt-get update || {
        echo "❌ apt-get update 失败"
        exit 1
    }
    echo "✅ apt 源已更新"
    
    echo ""
    echo "□ 安装 Redis 服务..."
    apt-get install redis-server -y || {
        echo "❌ Redis 安装失败"
        exit 1
    }
    echo "✅ Redis 已安装"
fi

echo ""

# ============================================================
# [2/4] 配置 Redis
# ============================================================
echo "[2/4] 配置 Redis"
echo "------------------------------------------------------------"

REDIS_CONF="/etc/redis/redis.conf"

if [ ! -f "$REDIS_CONF" ]; then
    echo "❌ Redis 配置文件不存在: $REDIS_CONF"
    echo "   请检查 Redis 安装是否正确"
    exit 1
fi

# 备份配置文件
if [ ! -f "${REDIS_CONF}.bak" ]; then
    echo "□ 备份 Redis 配置文件..."
    cp "$REDIS_CONF" "${REDIS_CONF}.bak"
    echo "✅ 配置文件已备份到: ${REDIS_CONF}.bak"
fi

# 启用 systemd 监督
echo "□ 配置 systemd 监督..."
if grep -q "^#*supervised" "$REDIS_CONF"; then
    # 如果存在 supervised 配置，修改它
    sed -i 's/^#*supervised .*/supervised systemd/' "$REDIS_CONF"
    echo "✅ 已启用 supervised systemd"
else
    # 如果不存在，添加配置
    echo "supervised systemd" >> "$REDIS_CONF"
    echo "✅ 已添加 supervised systemd 配置"
fi

# 确保 bind 127.0.0.1（安全配置）
echo "□ 配置 Redis 绑定地址..."
if grep -q "^#*bind" "$REDIS_CONF"; then
    # 如果存在 bind 配置，确保是 127.0.0.1
    if ! grep -q "^bind 127.0.0.1" "$REDIS_CONF"; then
        sed -i 's/^#*bind .*/bind 127.0.0.1/' "$REDIS_CONF"
        echo "✅ 已配置 bind 127.0.0.1"
    else
        echo "✅ bind 127.0.0.1 已配置"
    fi
else
    # 如果不存在，添加配置
    echo "bind 127.0.0.1" >> "$REDIS_CONF"
    echo "✅ 已添加 bind 127.0.0.1 配置"
fi

# 确保 protected-mode 启用（安全配置）
echo "□ 配置 Redis 保护模式..."
if grep -q "^#*protected-mode" "$REDIS_CONF"; then
    if ! grep -q "^protected-mode yes" "$REDIS_CONF"; then
        sed -i 's/^#*protected-mode .*/protected-mode yes/' "$REDIS_CONF"
        echo "✅ 已启用 protected-mode"
    else
        echo "✅ protected-mode 已启用"
    fi
else
    echo "protected-mode yes" >> "$REDIS_CONF"
    echo "✅ 已添加 protected-mode 配置"
fi

echo ""

# ============================================================
# [3/4] 启动并启用 Redis
# ============================================================
echo "[3/4] 启动并启用 Redis 服务"
echo "------------------------------------------------------------"

# 启动 Redis 服务
echo "□ 启动 Redis 服务..."
systemctl start redis-server || {
    echo "❌ 启动 Redis 服务失败"
    echo "   查看错误信息:"
    systemctl status redis-server --no-pager | head -20
    exit 1
}
echo "✅ Redis 服务已启动"

# 等待服务启动
sleep 2

# 设置开机自启
echo "□ 设置 Redis 开机自启..."
systemctl enable redis-server || {
    echo "⚠️  设置开机自启失败，但服务已启动"
}
echo "✅ Redis 已设置为开机自启"

# 检查服务状态
echo "□ 检查 Redis 服务状态..."
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis 服务运行中"
    systemctl status redis-server --no-pager | head -10
else
    echo "❌ Redis 服务未运行"
    systemctl status redis-server --no-pager
    exit 1
fi

echo ""

# ============================================================
# [4/4] 验证安装
# ============================================================
echo "[4/4] 验证 Redis 安装"
echo "------------------------------------------------------------"

# 测试 Redis 连接
echo "□ 测试 Redis 连接..."
if command -v redis-cli > /dev/null 2>&1; then
    PING_RESULT=$(redis-cli ping 2>&1)
    if [ "$PING_RESULT" = "PONG" ]; then
        echo "✅ Redis 连接正常 (返回: $PING_RESULT)"
    else
        echo "❌ Redis 连接失败 (返回: $PING_RESULT)"
        echo "   请检查 Redis 服务状态"
        exit 1
    fi
else
    echo "❌ redis-cli 命令未找到"
    exit 1
fi

# 测试 Redis 基本操作
echo "□ 测试 Redis 基本操作..."
TEST_KEY="redis_test_$(date +%s)"
if redis-cli set "$TEST_KEY" "test_value" > /dev/null 2>&1 && \
   redis-cli get "$TEST_KEY" > /dev/null 2>&1 && \
   redis-cli del "$TEST_KEY" > /dev/null 2>&1; then
    echo "✅ Redis 读写操作正常"
else
    echo "⚠️  Redis 读写操作测试失败，但连接正常"
fi

# 检查 Redis 版本信息
echo "□ Redis 版本信息:"
redis-cli --version || echo "无法获取版本信息"

echo ""

# ============================================================
# [5/5] 重启后端服务
# ============================================================
echo "[5/5] 重启后端 API 服务"
echo "------------------------------------------------------------"

# 检查后端服务是否存在
if systemctl list-unit-files | grep -q "luckyred-api.service"; then
    echo "□ 停止后端服务..."
    systemctl stop luckyred-api || {
        echo "⚠️  停止后端服务失败或服务未运行"
    }
    
    sleep 2
    
    echo "□ 启动后端服务..."
    systemctl start luckyred-api || {
        echo "❌ 启动后端服务失败"
        echo "   查看错误信息:"
        systemctl status luckyred-api --no-pager | head -20
        exit 1
    }
    
    sleep 2
    
    echo "□ 检查后端服务状态..."
    if systemctl is-active --quiet luckyred-api; then
        echo "✅ 后端服务运行中"
        systemctl status luckyred-api --no-pager | head -10
    else
        echo "❌ 后端服务未运行"
        systemctl status luckyred-api --no-pager | head -20
        echo ""
        echo "⚠️  后端服务启动失败，但 Redis 已成功安装和配置"
        echo "   请手动检查后端服务日志: sudo journalctl -u luckyred-api -n 50 --no-pager"
    fi
else
    echo "⚠️  后端服务 (luckyred-api) 未找到，跳过重启"
    echo "   请手动重启后端服务"
fi

echo ""

# ============================================================
# 总结
# ============================================================
echo "============================================================"
echo "Redis 安装和配置完成"
echo "结束时间: $(date)"
echo "============================================================"
echo ""
echo "安装总结:"
echo "✅ Redis 已安装"
echo "✅ Redis 配置已更新（supervised systemd, bind 127.0.0.1, protected-mode）"
echo "✅ Redis 服务已启动并设置为开机自启"
echo "✅ Redis 连接测试通过"

if systemctl is-active --quiet luckyred-api 2>/dev/null; then
    echo "✅ 后端服务已重启"
else
    echo "⚠️  后端服务状态异常，请检查日志"
fi

echo ""
echo "下一步操作:"
echo "1. 检查后端服务日志: sudo journalctl -u luckyred-api -n 50 --no-pager"
echo "2. 测试 API 端点: curl http://127.0.0.1:8000/api/v1/health"
echo "3. 在前端刷新页面，检查是否还有 500 错误"
echo "4. 如果仍有问题，运行: sudo bash scripts/server/fix_500_fatal.sh"
echo ""

