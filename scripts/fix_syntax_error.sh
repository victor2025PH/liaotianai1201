#!/bin/bash
# 修复 server_monitor.py 的语法错误
# 根据错误日志，第 246 行有语法错误

set -e

echo "=========================================="
echo "🔧 修复 server_monitor.py 语法错误"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

SERVER_MONITOR="$PROJECT_ROOT/admin-backend/app/core/server_monitor.py"

# 备份原文件
if [ -f "$SERVER_MONITOR" ]; then
    cp "$SERVER_MONITOR" "$SERVER_MONITOR.bak.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已备份原文件"
fi

# 检查第 246 行
echo "检查第 246 行..."
if sed -n '246p' "$SERVER_MONITOR" | grep -q "logger.warning.*{e}"; then
    echo "⚠️  发现错误的 logger.warning 语句，修复中..."
    # 修复错误的 logger.warning 为 logger.error
    sed -i '246s/logger\.warning.*{e}")/logger.error(f"收集服务器 {node_id} 指标失败: {e}")/' "$SERVER_MONITOR"
    echo "✅ 已修复第 246 行"
fi

# 检查第 188 行的转义序列警告
echo "检查第 188 行的转义序列..."
if sed -n '188p' "$SERVER_MONITOR" | grep -q "top -bn1"; then
    # 确保使用原始字符串（r""）
    if ! sed -n '188p' "$SERVER_MONITOR" | grep -q '^[[:space:]]*r"'; then
        echo "修复第 188 行的转义序列警告..."
        sed -i "188s/\"top -bn1/r\"top -bn1/" "$SERVER_MONITOR"
        echo "✅ 已修复第 188 行"
    fi
fi

# 验证 Python 语法
echo ""
echo "验证 Python 语法..."
cd "$PROJECT_ROOT/admin-backend" || exit 1
source .venv/bin/activate

if python3 -m py_compile "$SERVER_MONITOR" 2>&1; then
    echo "✅ Python 语法验证通过"
else
    echo "❌ Python 语法验证失败"
    echo "错误信息:"
    python3 -m py_compile "$SERVER_MONITOR" 2>&1 || true
    exit 1
fi

# 测试导入
echo ""
echo "测试导入 server_monitor..."
if python3 -c "from app.core.server_monitor import ServerMonitor; print('✅ 导入成功')" 2>&1 | grep -q "✅"; then
    echo "✅ server_monitor 可以正常导入"
else
    echo "❌ server_monitor 导入失败"
    python3 -c "from app.core.server_monitor import ServerMonitor" 2>&1
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 语法错误修复完成！"
echo "=========================================="
echo ""
echo "现在可以重新启动后端:"
echo "  pm2 restart backend"
echo ""

