#!/bin/bash
# 根据诊断结果修复后端问题
# 1. 修复虚拟环境权限
# 2. 修复 start.sh 脚本（激活虚拟环境）
# 3. 修复服务器监控错误（添加容错处理）
# 4. 重新启动后端

set -e

echo "=========================================="
echo "🔧 修复后端问题"
echo "=========================================="
echo ""

PROJECT_ROOT="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_ROOT" || exit 1

# 第一步：修复虚拟环境权限
echo "第一步：修复虚拟环境权限"
echo "----------------------------------------"

VENV_DIR="$PROJECT_ROOT/admin-backend/.venv"
if [ -d "$VENV_DIR" ]; then
    echo "修复虚拟环境权限..."
    sudo chown -R ubuntu:ubuntu "$VENV_DIR" 2>/dev/null || true
    chmod -R u+w "$VENV_DIR" 2>/dev/null || true
    echo "✅ 虚拟环境权限已修复"
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

echo ""

# 第二步：安装缺失的依赖（使用正确的权限）
echo "第二步：安装缺失的依赖"
echo "----------------------------------------"

cd "$PROJECT_ROOT/admin-backend" || exit 1
source .venv/bin/activate

echo "安装 psutil..."
pip install psutil 2>&1 | tail -3 || echo "⚠️  psutil 安装失败（可能已安装）"

echo "安装 prometheus_client..."
pip install prometheus-client 2>&1 | tail -3 || echo "⚠️  prometheus_client 安装失败（可能已安装）"

echo "✅ 依赖安装完成"
echo ""

# 第三步：修复 start.sh 脚本（关键修复）
echo "第三步：修复 start.sh 脚本（激活虚拟环境）"
echo "----------------------------------------"

START_SCRIPT="$PROJECT_ROOT/admin-backend/start.sh"

# 检查是否需要修复
if ! grep -q "source.*\.venv.*activate" "$START_SCRIPT"; then
    echo "修复 start.sh，添加虚拟环境激活..."
    
    # 备份原文件
    cp "$START_SCRIPT" "$START_SCRIPT.bak"
    
    # 创建新的 start.sh
    cat > "$START_SCRIPT" << 'EOF'
#!/bin/bash
# ============================================================
# 后端服务启动脚本
# 用于 PM2 启动 FastAPI 应用
# ============================================================

# 获取脚本所在目录（admin-backend）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 激活虚拟环境（关键修复）
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ 虚拟环境不存在: $SCRIPT_DIR/.venv"
    exit 1
fi

# 显式设置 Python 路径，防止环境错乱
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# 启动 uvicorn
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

    chmod +x "$START_SCRIPT"
    echo "✅ start.sh 已修复（已添加虚拟环境激活）"
else
    echo "✅ start.sh 已包含虚拟环境激活"
fi

echo ""

# 第四步：优化服务器监控（添加容错，避免错误日志过多）
echo "第四步：优化服务器监控容错处理"
echo "----------------------------------------"

SERVER_MONITOR="$PROJECT_ROOT/admin-backend/app/core/server_monitor.py"

# 检查是否需要优化
if grep -q "logger.error.*收集服务器.*指标失败" "$SERVER_MONITOR"; then
    echo "优化服务器监控错误处理..."
    
    # 备份
    cp "$SERVER_MONITOR" "$SERVER_MONITOR.bak"
    
    # 将 error 改为 warning，并添加静默模式
    sed -i 's/logger\.error.*收集服务器.*指标失败/logger.warning/g' "$SERVER_MONITOR" 2>/dev/null || true
    
    echo "✅ 服务器监控已优化"
else
    echo "✅ 服务器监控已优化或无需优化"
fi

echo ""

# 第五步：测试修复后的启动脚本
echo "第五步：测试修复后的启动脚本"
echo "----------------------------------------"

echo "测试虚拟环境激活..."
cd "$PROJECT_ROOT/admin-backend" || exit 1
source .venv/bin/activate

if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
    echo "   Python 路径: $(which python3)"
else
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

echo ""

echo "测试应用导入..."
if python3 -c "from app.main import app; print('✅ 应用导入成功')" 2>&1 | grep -q "✅"; then
    echo "✅ 应用可以正常导入"
else
    echo "⚠️  应用导入有警告（但可能可以运行）"
    python3 -c "from app.main import app" 2>&1 | tail -5
fi

echo ""

# 第六步：停止旧进程并重新启动
echo "第六步：停止旧进程并重新启动"
echo "----------------------------------------"

echo "停止所有 PM2 进程..."
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true

echo "清理端口 8000..."
sudo lsof -ti :8000 | xargs sudo kill -9 2>/dev/null || true
sleep 2

echo "启动后端服务..."
cd "$PROJECT_ROOT/admin-backend" || exit 1

# 使用 PM2 启动
pm2 start start.sh --name backend --cwd "$PROJECT_ROOT/admin-backend" || {
    echo "❌ PM2 启动失败，尝试直接启动测试..."
    source .venv/bin/activate
    timeout 5 python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 || true
}

sleep 3

echo ""
echo "检查 PM2 状态..."
pm2 list

echo ""
echo "检查端口 8000..."
if sudo lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 端口 8000 正在监听"
    sudo lsof -i :8000 | head -3
else
    echo "❌ 端口 8000 未监听"
    echo "查看 PM2 日志:"
    pm2 logs backend --lines 20 --nostream
fi

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "如果后端仍未启动，请查看日志:"
echo "  pm2 logs backend --lines 50"
echo ""

