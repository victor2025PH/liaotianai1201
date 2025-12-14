#!/bin/bash
# ============================================================
# 诊断账号 server_id 设置脚本
# ============================================================

set +e # 不在第一个错误时退出

echo "=========================================="
echo "🔍 诊断账号 server_id 设置"
echo "=========================================="
echo ""

# 项目根目录
PROJECT_DIR="/home/ubuntu/telegram-ai-system"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 错误: 找不到项目目录: $PROJECT_DIR"
    echo "请确保项目已部署到 $PROJECT_DIR"
    exit 1
fi

echo "项目目录: $PROJECT_DIR"
echo ""

# 数据库路径
DB_PATH="$PROJECT_DIR/admin-backend/data/app.db"

if [ ! -f "$DB_PATH" ]; then
    echo "❌ 错误: 数据库文件不存在: $DB_PATH"
    exit 1
fi

echo "数据库路径: $DB_PATH"
echo ""

# 检查 sqlite3 是否安装
if ! command -v sqlite3 &> /dev/null; then
    echo "❌ 错误: sqlite3 未安装。请运行: sudo apt install sqlite3"
    exit 1
fi

echo "[1/3] 检查数据库中的账号 server_id 设置..."
echo ""

# 查询所有账号的 server_id
echo "账号列表（包含 server_id）:"
echo "----------------------------------------"
sqlite3 "$DB_PATH" <<EOF
.mode column
.headers on
SELECT 
    account_id,
    phone_number,
    server_id,
    CASE 
        WHEN server_id IS NULL OR server_id = '' THEN '❌ 未设置'
        ELSE '✅ 已设置'
    END as status
FROM group_ai_accounts
ORDER BY account_id;
EOF

echo ""
echo "[2/3] 检查 Worker 节点上报的账号..."
echo ""

# 检查后端日志中是否有 Worker 节点上报的账号信息
LOG_FILE="$PROJECT_DIR/admin-backend/logs/app.log"
if [ -f "$LOG_FILE" ]; then
    echo "从日志中查找 Worker 节点上报的账号（最近 100 行）:"
    echo "----------------------------------------"
    grep -i "worker\|node\|heartbeat" "$LOG_FILE" | tail -20 | head -10
    echo ""
else
    echo "⚠️  日志文件不存在: $LOG_FILE"
    echo ""
fi

echo "[3/3] 检查系统服务状态..."
echo ""

# 检查后端服务状态
if systemctl is-active --quiet luckyred-api; then
    echo "✅ 后端服务 (luckyred-api) 正在运行"
else
    echo "❌ 后端服务 (luckyred-api) 未运行"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果发现账号的 server_id 为空，请："
echo "1. 确保 Worker 节点正在运行并发送心跳"
echo "2. 检查 Worker 节点是否正确上报账号信息"
echo "3. 检查后端日志: sudo journalctl -u luckyred-api -n 100 --no-pager"
echo ""

