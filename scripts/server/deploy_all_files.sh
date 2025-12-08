#!/bin/bash
# 完整部署脚本 - 拉取所有文件并设置环境

set -e

echo "============================================================"
echo "完整部署脚本 - 拉取所有文件"
echo "============================================================"

PROJECT_DIR="/home/ubuntu/telegram-ai-system"
cd "$PROJECT_DIR"

# 1. 拉取最新代码
echo ""
echo "=== 步骤1: 拉取最新代码 ==="
git fetch origin
git pull origin main
echo "✓ 代码拉取完成"

# 2. 检查并创建虚拟环境
echo ""
echo "=== 步骤2: 检查虚拟环境 ==="
if [ ! -d "admin-backend/venv" ]; then
    echo "创建Python虚拟环境..."
    cd admin-backend
    python3.12 -m venv venv
    cd ..
    echo "✓ 虚拟环境已创建"
else
    echo "✓ 虚拟环境已存在"
fi

# 3. 激活虚拟环境并安装依赖
echo ""
echo "=== 步骤3: 安装Python依赖 ==="
cd admin-backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
echo "✓ Python依赖安装完成"

# 4. 检查所有关键脚本文件
echo ""
echo "=== 步骤4: 检查关键脚本文件 ==="

SCRIPTS=(
    "scripts/server/generate_jwt_secret.py"
    "scripts/server/update_security_config.py"
    "scripts/server/quick_fix_security.sh"
    "scripts/server/configure_notifications.py"
    "scripts/server/performance_benchmark.py"
    "scripts/server/system_health_check.py"
    "scripts/server/check_database_performance.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "✓ $script"
        chmod +x "$script" 2>/dev/null || true
    else
        echo "✗ $script - 文件不存在！"
    fi
done

# 5. 检查文档文件
echo ""
echo "=== 步骤5: 检查文档文件 ==="

DOCS=(
    "docs/SECURITY_CONFIGURATION_GUIDE.md"
    "docs/NOTIFICATION_SETUP_GUIDE.md"
    "docs/TASK_COMPLETION_SUMMARY.md"
    "docs/DEPLOYMENT_STATUS.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "✓ $doc"
    else
        echo "✗ $doc - 文件不存在！"
    fi
done

# 6. 检查ecosystem.config.js
echo ""
echo "=== 步骤6: 检查PM2配置 ==="
if [ -f "ecosystem.config.js" ]; then
    echo "✓ ecosystem.config.js"
else
    echo "✗ ecosystem.config.js - 文件不存在！"
fi

# 7. 总结
echo ""
echo "============================================================"
echo "部署检查完成"
echo "============================================================"
echo ""
echo "下一步操作："
echo ""
echo "1. 激活虚拟环境并运行脚本："
echo "   cd admin-backend"
echo "   source venv/bin/activate"
echo "   python3 ../scripts/server/update_security_config.py"
echo ""
echo "2. 配置通知渠道："
echo "   python3 ../scripts/server/configure_notifications.py"
echo ""
echo "3. 运行性能基准测试："
echo "   python3 ../scripts/server/performance_benchmark.py"
echo ""
echo "4. 重启服务（如果需要）："
echo "   pm2 restart all"
echo ""

