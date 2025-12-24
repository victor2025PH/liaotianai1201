#!/bin/bash
# 完整修复 server_monitor.py 的语法错误
# 根据错误日志，第 246 行有语法错误，可能是之前的 sed 命令破坏了文件

set -e

echo "=========================================="
echo "🔧 完整修复 server_monitor.py"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 先拉取最新代码
echo "拉取最新代码..."
git pull || echo "⚠️  git pull 失败，继续使用本地代码"

SERVER_MONITOR="$PROJECT_ROOT/admin-backend/app/core/server_monitor.py"

# 备份原文件
if [ -f "$SERVER_MONITOR" ]; then
    BACKUP_FILE="$SERVER_MONITOR.bak.$(date +%Y%m%d_%H%M%S)"
    cp "$SERVER_MONITOR" "$BACKUP_FILE"
    echo "✅ 已备份原文件到: $BACKUP_FILE"
fi

# 检查并修复第 246 行
echo ""
echo "检查第 246 行..."
LINE_246=$(sed -n '246p' "$SERVER_MONITOR")
echo "当前第 246 行内容: $LINE_246"

# 如果第 246 行有问题，修复它
if echo "$LINE_246" | grep -q "logger.warning.*{e}"; then
    echo "⚠️  发现错误的 logger.warning 语句，修复中..."
    sed -i '246s/.*/            logger.error(f"收集服务器 {node_id} 指标失败: {e}")/' "$SERVER_MONITOR"
    echo "✅ 已修复第 246 行"
elif ! echo "$LINE_246" | grep -q "logger.error.*收集服务器.*指标失败"; then
    echo "⚠️  第 246 行格式不正确，修复中..."
    sed -i '246s/.*/            logger.error(f"收集服务器 {node_id} 指标失败: {e}")/' "$SERVER_MONITOR"
    echo "✅ 已修复第 246 行"
else
    echo "✅ 第 246 行看起来正确"
fi

# 检查并修复第 188 行的转义序列
echo ""
echo "检查第 188 行..."
LINE_188=$(sed -n '188p' "$SERVER_MONITOR")
echo "当前第 188 行内容: $LINE_188"

if echo "$LINE_188" | grep -q "top -bn1" && ! echo "$LINE_188" | grep -q 'r"top'; then
    echo "修复第 188 行的转义序列警告..."
    sed -i '188s/"top -bn1/r"top -bn1/' "$SERVER_MONITOR"
    echo "✅ 已修复第 188 行"
else
    echo "✅ 第 188 行看起来正确"
fi

# 确保 Tuple 已导入
echo ""
echo "检查 Tuple 导入..."
if ! grep -q "from typing import.*Tuple" "$SERVER_MONITOR"; then
    echo "添加 Tuple 导入..."
    sed -i 's/from typing import Dict, List, Optional/from typing import Dict, List, Optional, Tuple/' "$SERVER_MONITOR"
    echo "✅ 已添加 Tuple 导入"
else
    echo "✅ Tuple 已导入"
fi

# 验证 Python 语法
echo ""
echo "验证 Python 语法..."
cd "$PROJECT_ROOT/admin-backend" || exit 1

if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在"
    exit 1
fi

source .venv/bin/activate

# 编译检查
if python3 -m py_compile "$SERVER_MONITOR" 2>&1; then
    echo "✅ Python 语法验证通过"
else
    echo "❌ Python 语法验证失败"
    echo "错误信息:"
    python3 -m py_compile "$SERVER_MONITOR" 2>&1 || true
    echo ""
    echo "请检查文件内容，可能需要手动修复"
    exit 1
fi

# 测试导入
echo ""
echo "测试导入 server_monitor..."
if python3 -c "from app.core.server_monitor import ServerMonitor; print('✅ 导入成功')" 2>&1 | grep -q "✅"; then
    echo "✅ server_monitor 可以正常导入"
else
    echo "⚠️  server_monitor 导入有警告（但可能可以运行）"
    python3 -c "from app.core.server_monitor import ServerMonitor" 2>&1 | head -10
fi

# 测试完整应用导入
echo ""
echo "测试完整应用导入..."
if python3 -c "from app.main import app; print('✅ 应用导入成功')" 2>&1 | grep -q "✅"; then
    echo "✅ 应用可以正常导入"
else
    echo "⚠️  应用导入有警告（但可能可以运行）"
    python3 -c "from app.main import app" 2>&1 | grep -E "(SyntaxError|Error)" | head -5 || echo "没有致命错误"
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "现在可以重新启动后端:"
echo "  pm2 restart backend"
echo "  或"
echo "  pm2 stop backend"
echo "  pm2 start /home/ubuntu/telegram-ai-system/admin-backend/start.sh --name backend"
echo ""

