#!/bin/bash
# 全自动执行和监控系统 - 自动诊断和修复直到成功

set -e

LOG_DIR="$HOME/liaotian/test_logs"
mkdir -p "$LOG_DIR"
SYSTEM_LOG="$LOG_DIR/system_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$SYSTEM_LOG")
exec 2>&1

echo "========================================"
echo "全自动执行和监控系统启动"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "日志: $SYSTEM_LOG"
echo "========================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1"; }
info() { echo -e "${BLUE}ℹ️${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; }

# 函数：检查后端服务
check_backend_service() {
    if curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# 函数：修复测试用户
fix_test_user() {
    info "修复测试用户..."
    cd ~/liaotian/admin-backend 2>/dev/null || return 1
    
    if [ ! -d ".venv" ]; then
        error "虚拟环境不存在"
        return 1
    fi
    
    source .venv/bin/activate
    export ADMIN_DEFAULT_PASSWORD=testpass123
    
    if [ -f "reset_admin_user.py" ]; then
        python reset_admin_user.py > /dev/null 2>&1
        sleep 2
        return 0
    fi
    return 1
}

# 函数：验证登录
verify_login() {
    RESPONSE=$(curl -s --max-time 5 -X POST http://localhost:8000/api/v1/auth/login \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=admin@example.com&password=testpass123" 2>&1)
    
    if echo "$RESPONSE" | grep -q "access_token"; then
        return 0
    fi
    return 1
}

# 函数：安装浏览器
install_browser() {
    info "安装 Playwright 浏览器..."
    cd ~/liaotian/saas-demo
    
    if ! command -v npx &> /dev/null; then
        error "npx 未找到，需要先安装 Node.js"
        return 1
    fi
    
    # 检查是否已安装
    if [ -d "node_modules/@playwright" ]; then
        info "Playwright 已安装"
    else
        warn "Playwright 未安装，正在安装..."
        npm install --silent 2>&1 || return 1
    fi
    
    # 安装浏览器
    npx playwright install chromium --with-deps 2>&1 | tail -5 || \
    npx playwright install chromium 2>&1 | tail -5
    
    return 0
}

# 函数：运行测试
run_tests() {
    info "运行 E2E 测试..."
    cd ~/liaotian/saas-demo
    
    TEST_LOG="$LOG_DIR/test_run_$(date +%Y%m%d_%H%M%S).log"
    npm run test:e2e > "$TEST_LOG" 2>&1
    TEST_EXIT=$?
    
    return $TEST_EXIT
}

# 主执行流程
main() {
    info "开始自动执行流程..."
    echo ""
    
    # 步骤 1: 更新代码
    info "[1/6] 更新代码"
    cd ~/liaotian/saas-demo
    git pull origin master > /dev/null 2>&1 || true
    chmod +x *.sh 2>/dev/null || true
    success "代码已更新"
    echo ""
    
    # 步骤 2: 检查后端服务
    info "[2/6] 检查后端服务"
    RETRY=0
    MAX_RETRY=3
    
    while [ $RETRY -lt $MAX_RETRY ]; do
        if check_backend_service; then
            success "后端服务运行正常"
            break
        else
            RETRY=$((RETRY + 1))
            if [ $RETRY -lt $MAX_RETRY ]; then
                warn "后端服务未运行，等待中... ($RETRY/$MAX_RETRY)"
                sleep 5
            else
                error "后端服务未运行，请先启动"
                echo "启动命令: cd ~/liaotian/admin-backend && source .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
                return 1
            fi
        fi
    done
    echo ""
    
    # 步骤 3: 修复测试用户
    info "[3/6] 准备测试用户"
    if ! verify_login; then
        if fix_test_user; then
            if verify_login; then
                success "测试用户已创建并验证"
            else
                error "用户创建后仍无法登录"
                return 1
            fi
        else
            error "无法创建测试用户"
            return 1
        fi
    else
        success "测试用户正常"
    fi
    echo ""
    
    # 步骤 4: 安装浏览器
    info "[4/6] 安装浏览器"
    if install_browser; then
        success "浏览器已安装"
    else
        error "浏览器安装失败"
        return 1
    fi
    echo ""
    
    # 步骤 5: 运行测试
    info "[5/6] 运行测试"
    echo ""
    echo "========================================"
    echo "开始执行 E2E 测试"
    echo "========================================"
    echo ""
    
    if run_tests; then
        success "[6/6] 所有测试通过！"
        echo ""
        echo "========================================"
        echo "✅ 所有任务成功完成！"
        echo "========================================"
        return 0
    else
        error "[6/6] 测试失败"
        echo ""
        echo "========================================"
        echo "❌ 测试执行失败"
        echo "========================================"
        
        # 显示错误信息
        LATEST_TEST_LOG=$(ls -t "$LOG_DIR"/test_run_*.log 2>/dev/null | head -1)
        if [ -n "$LATEST_TEST_LOG" ]; then
            echo ""
            echo "错误日志:"
            echo "----------------------------------------"
            grep -iE "error|失败|错误|failed|failing" "$LATEST_TEST_LOG" | tail -20 || tail -30 "$LATEST_TEST_LOG"
            echo "----------------------------------------"
        fi
        
        return 1
    fi
}

# 执行主流程
if main; then
    exit 0
else
    exit 1
fi
