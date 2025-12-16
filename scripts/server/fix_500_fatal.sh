#!/bin/bash
# ============================================================
# 500 Internal Server Error 急救脚本
# ============================================================
# 
# 功能：
# 1. 修复文件权限（SQLite 数据库等）
# 2. 重启 Redis 服务
# 3. 重启后端 API 服务
# 4. 查看日志确认问题是否解决
#
# 使用方法：sudo bash scripts/server/fix_500_fatal.sh
# ============================================================

set -e  # 遇到错误立即退出

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
DATA_DIR="$BACKEND_DIR/data"
DB_FILE="$DATA_DIR/app.db"

echo "============================================================"
echo "500 Internal Server Error 急救脚本"
echo "============================================================"
echo "开始时间: $(date)"
echo ""

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  警告：建议以 root 权限运行此脚本（使用 sudo）"
    echo "继续执行..."
    echo ""
fi

# ============================================================
# [1/4] 暴力修复权限（最关键）
# ============================================================
echo "[1/4] 修复文件权限"
echo "------------------------------------------------------------"

# 修复项目目录权限
echo "□ 修复项目目录权限: $PROJECT_DIR"
if [ -d "$PROJECT_DIR" ]; then
    chown -R ubuntu:ubuntu "$PROJECT_DIR" || {
        echo "⚠️  权限修复失败，尝试使用 sudo..."
        sudo chown -R ubuntu:ubuntu "$PROJECT_DIR" || {
            echo "❌ 权限修复失败，请手动检查"
            exit 1
        }
    }
    echo "✅ 项目目录权限已修复"
else
    echo "❌ 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

# 修复数据目录权限
echo "□ 修复数据目录权限: $DATA_DIR"
if [ -d "$DATA_DIR" ]; then
    chown -R ubuntu:ubuntu "$DATA_DIR" || sudo chown -R ubuntu:ubuntu "$DATA_DIR"
    chmod -R 755 "$DATA_DIR" || sudo chmod -R 755 "$DATA_DIR"
    echo "✅ 数据目录权限已修复"
else
    echo "⚠️  数据目录不存在，创建中..."
    mkdir -p "$DATA_DIR" || sudo mkdir -p "$DATA_DIR"
    chown -R ubuntu:ubuntu "$DATA_DIR" || sudo chown -R ubuntu:ubuntu "$DATA_DIR"
    chmod -R 755 "$DATA_DIR" || sudo chmod -R 755 "$DATA_DIR"
    echo "✅ 数据目录已创建并设置权限"
fi

# 修复数据库文件权限
if [ -f "$DB_FILE" ]; then
    echo "□ 修复数据库文件权限: $DB_FILE"
    chown ubuntu:ubuntu "$DB_FILE" || sudo chown ubuntu:ubuntu "$DB_FILE"
    chmod 664 "$DB_FILE" || sudo chmod 664 "$DB_FILE"
    echo "✅ 数据库文件权限已修复"
    
    # 检查数据库文件是否可写
    if [ -w "$DB_FILE" ]; then
        echo "✅ 数据库文件可写"
    else
        echo "⚠️  警告：数据库文件可能仍不可写"
        # 尝试移除只读属性
        chmod +w "$DB_FILE" || sudo chmod +w "$DB_FILE"
    fi
else
    echo "⚠️  数据库文件不存在: $DB_FILE"
    echo "   这可能是正常的（如果数据库尚未初始化）"
fi

# 修复所有 .db 文件权限
echo "□ 修复所有 .db 文件权限"
find "$DATA_DIR" -name "*.db" -o -name "*.db-journal" 2>/dev/null | while read db_file; do
    if [ -f "$db_file" ]; then
        chown ubuntu:ubuntu "$db_file" || sudo chown ubuntu:ubuntu "$db_file"
        chmod 664 "$db_file" || sudo chmod 664 "$db_file"
        echo "  ✅ 已修复: $db_file"
    fi
done

echo ""

# ============================================================
# [2/4] 强制重启 Redis
# ============================================================
echo "[2/4] 重启 Redis 服务"
echo "------------------------------------------------------------"

# 检查 Redis 是否安装
if ! command -v redis-cli > /dev/null 2>&1; then
    echo "⚠️  Redis CLI 未找到，跳过 Redis 重启"
else
    # 停止 Redis
    echo "□ 停止 Redis 服务..."
    systemctl stop redis-server 2>/dev/null || sudo systemctl stop redis-server 2>/dev/null || {
        echo "⚠️  停止 Redis 失败或服务未运行"
    }
    
    sleep 2
    
    # 启动 Redis
    echo "□ 启动 Redis 服务..."
    systemctl start redis-server 2>/dev/null || sudo systemctl start redis-server 2>/dev/null || {
        echo "❌ 启动 Redis 失败"
        echo "   尝试检查 Redis 配置: sudo systemctl status redis-server"
    }
    
    sleep 2
    
    # 检查 Redis 状态
    echo "□ 检查 Redis 服务状态..."
    if systemctl is-active --quiet redis-server || sudo systemctl is-active --quiet redis-server; then
        echo "✅ Redis 服务运行中"
        systemctl status redis-server --no-pager | head -7 || sudo systemctl status redis-server --no-pager | head -7
    else
        echo "❌ Redis 服务未运行"
        systemctl status redis-server --no-pager || sudo systemctl status redis-server --no-pager
    fi
    
    # 测试 Redis 连接
    echo "□ 测试 Redis 连接..."
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis 连接正常"
    else
        echo "⚠️  Redis 连接失败，可能需要检查配置"
    fi
fi

echo ""

# ============================================================
# [3/4] 重启后端 API
# ============================================================
echo "[3/4] 重启后端 API 服务"
echo "------------------------------------------------------------"

# 停止后端服务
echo "□ 停止后端服务..."
systemctl stop luckyred-api 2>/dev/null || sudo systemctl stop luckyred-api 2>/dev/null || {
    echo "⚠️  停止后端服务失败或服务未运行"
}

sleep 2

# 启动后端服务
echo "□ 启动后端服务..."
systemctl start luckyred-api 2>/dev/null || sudo systemctl start luckyred-api 2>/dev/null || {
    echo "❌ 启动后端服务失败"
    echo "   请检查服务配置: sudo systemctl status luckyred-api"
}

sleep 2

# 检查后端服务状态
echo "□ 检查后端服务状态..."
if systemctl is-active --quiet luckyred-api || sudo systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务运行中"
    systemctl status luckyred-api --no-pager | head -7 || sudo systemctl status luckyred-api --no-pager | head -7
else
    echo "❌ 后端服务未运行"
    systemctl status luckyred-api --no-pager || sudo systemctl status luckyred-api --no-pager
fi

echo ""

# ============================================================
# [4/4] 查看实时报错日志
# ============================================================
echo "[4/4] 查看服务日志（等待 5 秒让服务完全启动）"
echo "------------------------------------------------------------"
echo "等待服务启动..."
sleep 5

echo ""
echo "后端服务日志（最后 50 行）:"
echo "============================================================"
journalctl -u luckyred-api -n 50 --no-pager 2>/dev/null || sudo journalctl -u luckyred-api -n 50 --no-pager

echo ""
echo "============================================================"
echo "日志分析"
echo "============================================================"

# 检查是否有错误
ERROR_COUNT=$(journalctl -u luckyred-api -n 50 --no-pager 2>/dev/null | grep -i "error\|exception\|traceback\|failed" | wc -l || echo "0")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  发现 $ERROR_COUNT 个可能的错误/异常"
    echo ""
    echo "最近的错误:"
    journalctl -u luckyred-api -n 50 --no-pager 2>/dev/null | grep -i "error\|exception\|traceback\|failed" | tail -5 || true
else
    echo "✅ 未发现明显的错误信息"
fi

echo ""
echo "============================================================"
echo "服务状态总结"
echo "============================================================"

# Redis 状态
if systemctl is-active --quiet redis-server 2>/dev/null || sudo systemctl is-active --quiet redis-server 2>/dev/null; then
    echo "✅ Redis: 运行中"
else
    echo "❌ Redis: 未运行"
fi

# 后端服务状态
if systemctl is-active --quiet luckyred-api 2>/dev/null || sudo systemctl is-active --quiet luckyred-api 2>/dev/null; then
    echo "✅ 后端 API: 运行中"
    
    # 检查端口
    if ss -tlnp 2>/dev/null | grep -q ":8000" || sudo ss -tlnp 2>/dev/null | grep -q ":8000"; then
        echo "✅ 端口 8000: 监听中"
    else
        echo "⚠️  端口 8000: 未监听"
    fi
else
    echo "❌ 后端 API: 未运行"
fi

# 数据库文件权限
if [ -f "$DB_FILE" ]; then
    if [ -r "$DB_FILE" ] && [ -w "$DB_FILE" ]; then
        echo "✅ 数据库文件: 可读写"
    else
        echo "❌ 数据库文件: 权限异常"
    fi
else
    echo "⚠️  数据库文件: 不存在（可能尚未初始化）"
fi

echo ""
echo "============================================================"
echo "急救脚本执行完成"
echo "结束时间: $(date)"
echo "============================================================"
echo ""
echo "下一步操作建议:"
echo "1. 如果仍有错误，请查看完整日志: sudo journalctl -u luckyred-api -n 100 --no-pager"
echo "2. 测试 API 端点: curl http://127.0.0.1:8000/api/v1/health"
echo "3. 检查前端是否能正常访问"
echo "4. 如果问题持续，请检查数据库文件完整性: sqlite3 $DB_FILE 'PRAGMA integrity_check;'"
echo ""

