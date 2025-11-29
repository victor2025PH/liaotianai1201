#!/bin/bash
# 服务器端实时监控执行脚本
# 自动执行、监控、修复直到成功

set -e

LOG_DIR="$HOME/liaotian/test_logs"
mkdir -p "$LOG_DIR"
MONITOR_LOG="$LOG_DIR/realtime_monitor_$(date +%Y%m%d_%H%M%S).log"
STATUS_FILE="$LOG_DIR/current_status.txt"

# 实时写入日志
exec > >(tee -a "$MONITOR_LOG")
exec 2>&1

echo "========================================"
echo "实时监控执行系统启动"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "监控日志: $MONITOR_LOG"
echo "========================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { 
    echo -e "${GREEN}✅${NC} $1"
    echo "[SUCCESS] $1" > "$STATUS_FILE"
}
error() { 
    echo -e "${RED}❌${NC} $1"
    echo "[ERROR] $1" > "$STATUS_FILE"
}
info() { 
    echo -e "${BLUE}ℹ️${NC} $1"
    echo "[INFO] $1" > "$STATUS_FILE"
}
step() { 
    echo -e "${YELLOW}[步骤]${NC} $1"
    echo "[STEP] $1" > "$STATUS_FILE"
}

# 函数：更新状态文件
update_status() {
    echo "$(date '+%Y-%m-%d %H:%M:%S')|$1|$2" >> "$LOG_DIR/status_history.txt"
}

# 函数：检查后端服务
check_backend() {
    if curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

# 函数：修复测试用户
fix_user() {
    info "修复测试用户..."
    cd ~/liaotian/admin-backend || return 1
    
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
    info "检查并安装浏览器..."
    cd ~/liaotian/saas-demo || return 1
    
    if [ ! -d "node_modules/@playwright" ]; then
        info "安装 Playwright..."
        npm install --silent 2>&1 || return 1
    fi
    
    npx playwright install chromium --with-deps 2>&1 | tail -5 || \
    npx playwright install chromium 2>&1 | tail -5
    
    return 0
}

# 主执行循环
MAX_ATTEMPTS=5
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    echo ""
    echo "========================================"
    echo "执行尝试 #$ATTEMPT/$MAX_ATTEMPTS"
    echo "========================================"
    echo ""
    
    # 步骤 1: 更新代码
    step "1. 更新代码"
    cd ~/liaotian/saas-demo
    git pull origin master > /dev/null 2>&1 || true
    chmod +x *.sh 2>/dev/null || true
    success "代码已更新"
    update_status "STEP_1" "代码已更新"
    
    # 步骤 2: 检查后端
    step "2. 检查后端服务"
    RETRY=0
    while [ $RETRY -lt 3 ]; do
        if check_backend; then
            success "后端服务正常"
            update_status "STEP_2" "后端服务正常"
            break
        else
            RETRY=$((RETRY + 1))
            if [ $RETRY -lt 3 ]; then
                info "后端服务未运行，等待中... ($RETRY/3)"
                sleep 5
            else
                error "后端服务未运行，请先启动"
                update_status "STEP_2" "后端服务未运行"
                exit 1
            fi
        fi
    done
    
    # 步骤 3: 修复用户
    step "3. 准备测试用户"
    if ! verify_login; then
        if fix_user; then
            if verify_login; then
                success "测试用户已创建并验证"
                update_status "STEP_3" "测试用户正常"
            else
                error "用户创建后仍无法登录"
                update_status "STEP_3" "登录失败"
                continue
            fi
        else
            error "无法创建测试用户"
            update_status "STEP_3" "创建用户失败"
            continue
        fi
    else
        success "测试用户正常"
        update_status "STEP_3" "测试用户正常"
    fi
    
    # 步骤 4: 安装浏览器
    step "4. 安装浏览器"
    if install_browser; then
        success "浏览器已安装"
        update_status "STEP_4" "浏览器已安装"
    else
        error "浏览器安装失败"
        update_status "STEP_4" "浏览器安装失败"
        continue
    fi
    
    # 步骤 5: 运行测试
    step "5. 运行 E2E 测试"
    echo ""
    echo "========================================"
    echo "开始运行测试..."
    echo "========================================"
    echo ""
    
    update_status "STEP_5" "开始运行测试"
    
    TEST_LOG="$LOG_DIR/test_output_$(date +%Y%m%d_%H%M%S).log"
    npm run test:e2e > "$TEST_LOG" 2>&1
    TEST_EXIT=$?
    
    # 检查测试结果
    if [ $TEST_EXIT -eq 0 ]; then
        success "所有测试通过！"
        update_status "COMPLETE" "所有测试通过"
        echo ""
        echo "========================================"
        echo "✅ 所有任务成功完成！"
        echo "========================================"
        echo ""
        echo "测试日志: $TEST_LOG"
        echo "监控日志: $MONITOR_LOG"
        exit 0
    else
        error "测试失败，退出码: $TEST_EXIT"
        update_status "STEP_5" "测试失败"
        
        # 分析错误
        info "分析错误..."
        if grep -qi "timeout\|timed out" "$TEST_LOG"; then
            info "发现超时错误，将增加超时时间..."
        fi
        if grep -qi "auth\|login\|unauthorized" "$TEST_LOG"; then
            info "发现认证错误，将重新创建用户..."
        fi
        if grep -qi "not found\|missing" "$TEST_LOG"; then
            info "发现文件缺失错误..."
        fi
        
        echo ""
        echo "错误摘要:"
        echo "----------------------------------------"
        grep -iE "error|失败|错误|failed|failing" "$TEST_LOG" | tail -10 || tail -20 "$TEST_LOG"
        echo "----------------------------------------"
        echo ""
        
        if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
            info "准备重试..."
            sleep 5
        fi
    fi
done

error "达到最大重试次数，执行失败"
update_status "FAILED" "达到最大重试次数"
exit 1
