#!/bin/bash
# ============================================================
# 后端服务问题诊断脚本
# ============================================================
# 
# 功能：
# 1. 检查后端服务状态
# 2. 查看后端日志
# 3. 检查端口和进程
# 4. 验证虚拟环境和依赖
# 
# 使用方法：
#   bash scripts/server/diagnose-backend-issue.sh
# ============================================================

set +e  # 不因为错误退出，收集所有诊断信息

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

success_msg() { echo -e "${GREEN}✅ $1${NC}"; }
error_msg() { echo -e "${RED}❌ $1${NC}"; }
info_msg() { echo -e "${YELLOW}ℹ️  $1${NC}"; }
step_msg() { echo -e "${BLUE}📌 $1${NC}"; }

PROJECT_DIR="/home/deployer/telegram-ai-system"
BACKEND_DIR="$PROJECT_DIR/admin-backend"
VENV_DIR="$BACKEND_DIR/venv"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 后端服务诊断"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================
# 1. 检查 PM2 状态
# ============================================================
step_msg "1. 检查 PM2 后端服务状态..."
echo ""
pm2 list | grep -A 5 "backend" || error_msg "未找到 backend 服务"
echo ""

# ============================================================
# 2. 检查端口监听
# ============================================================
step_msg "2. 检查端口 8000 监听状态..."
echo ""
if ss -tlnp 2>/dev/null | grep -q ":8000"; then
    success_msg "端口 8000 正在监听"
    ss -tlnp | grep ":8000"
else
    error_msg "端口 8000 未监听"
fi
echo ""

# ============================================================
# 3. 检查后端日志（最后 50 行）
# ============================================================
step_msg "3. 查看后端日志（最后 50 行）..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PM2 日志（标准输出）："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pm2 logs backend --lines 50 --nostream 2>&1 | tail -50
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PM2 日志（错误输出）："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pm2 logs backend --err --lines 50 --nostream 2>&1 | tail -50
echo ""

if [ -f "$PROJECT_DIR/logs/backend-error.log" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "错误日志文件："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -50 "$PROJECT_DIR/logs/backend-error.log"
    echo ""
fi

if [ -f "$PROJECT_DIR/logs/backend-out.log" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "标准输出日志文件："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -50 "$PROJECT_DIR/logs/backend-out.log"
    echo ""
fi

# ============================================================
# 4. 检查虚拟环境
# ============================================================
step_msg "4. 检查虚拟环境..."
echo ""
if [ -d "$VENV_DIR" ]; then
    success_msg "虚拟环境目录存在: $VENV_DIR"
    
    if [ -f "$VENV_DIR/bin/uvicorn" ]; then
        success_msg "uvicorn 可执行文件存在"
    else
        error_msg "uvicorn 可执行文件不存在: $VENV_DIR/bin/uvicorn"
    fi
    
    if [ -f "$VENV_DIR/bin/activate" ]; then
        success_msg "activate 脚本存在"
    else
        error_msg "activate 脚本不存在"
    fi
else
    error_msg "虚拟环境目录不存在: $VENV_DIR"
fi
echo ""

# ============================================================
# 5. 检查 Python 和依赖
# ============================================================
step_msg "5. 检查 Python 环境和依赖..."
echo ""
if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON_VERSION=$("$VENV_DIR/bin/python" --version 2>&1)
    success_msg "Python 版本: $PYTHON_VERSION"
else
    error_msg "虚拟环境中的 Python 不存在"
fi

if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    info_msg "requirements.txt 存在"
    echo "检查关键依赖..."
    if "$VENV_DIR/bin/pip" list 2>/dev/null | grep -q "uvicorn"; then
        success_msg "uvicorn 已安装"
    else
        error_msg "uvicorn 未安装"
    fi
    
    if "$VENV_DIR/bin/pip" list 2>/dev/null | grep -q "fastapi"; then
        success_msg "fastapi 已安装"
    else
        error_msg "fastapi 未安装"
    fi
else
    error_msg "requirements.txt 不存在"
fi
echo ""

# ============================================================
# 6. 检查应用文件
# ============================================================
step_msg "6. 检查应用文件..."
echo ""
if [ -f "$BACKEND_DIR/app/main.py" ]; then
    success_msg "main.py 存在"
else
    error_msg "main.py 不存在: $BACKEND_DIR/app/main.py"
fi

if [ -d "$BACKEND_DIR/app" ]; then
    info_msg "app 目录内容："
    ls -la "$BACKEND_DIR/app" | head -10
else
    error_msg "app 目录不存在"
fi
echo ""

# ============================================================
# 7. 尝试手动启动测试
# ============================================================
step_msg "7. 测试手动启动（5秒后停止）..."
echo ""
info_msg "尝试手动启动后端服务（将运行 5 秒以查看启动日志）..."
echo ""

cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"

# 设置超时，5秒后自动停止
timeout 5 "$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 2>&1 &
TEST_PID=$!
sleep 6
kill $TEST_PID 2>/dev/null || true

deactivate
cd "$PROJECT_DIR"
echo ""

# ============================================================
# 8. 检查进程
# ============================================================
step_msg "8. 检查相关进程..."
echo ""
ps aux | grep -E "uvicorn|python.*app.main" | grep -v grep || info_msg "未找到相关进程"
echo ""

# ============================================================
# 9. 检查端口占用
# ============================================================
step_msg "9. 检查端口 8000 占用情况..."
echo ""
if sudo lsof -i :8000 2>/dev/null; then
    info_msg "端口 8000 被占用"
else
    info_msg "端口 8000 未被占用"
fi
echo ""

# ============================================================
# 总结和建议
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 诊断总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
info_msg "请查看上述输出，重点关注："
echo "  1. PM2 日志中的错误信息"
echo "  2. 虚拟环境和依赖是否完整"
echo "  3. 应用文件是否存在"
echo "  4. 手动启动时的错误信息"
echo ""
info_msg "如果发现问题，请根据错误信息修复后，运行："
echo "  pm2 restart backend"
echo "  或"
echo "  pm2 delete backend && pm2 start ecosystem.config.js"
echo ""
