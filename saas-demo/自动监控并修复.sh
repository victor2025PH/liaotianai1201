#!/bin/bash
# 自动监控测试进度并修复错误

LOG_DIR="$HOME/liaotian/test_logs"
mkdir -p "$LOG_DIR"
MONITOR_LOG="$LOG_DIR/monitor_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$MONITOR_LOG")
exec 2>&1

echo "========================================"
echo "自动监控和修复系统启动"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ️${NC} $1"
}

# 函数：检查后端服务
check_backend() {
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 函数：检查测试用户
check_test_user() {
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=admin@example.com&password=testpass123")
    
    if echo "$RESPONSE" | grep -q "access_token"; then
        return 0
    else
        return 1
    fi
}

# 函数：创建/修复测试用户
fix_test_user() {
    print_info "正在创建/修复测试用户..."
    cd ~/liaotian/admin-backend
    
    if [ ! -d ".venv" ]; then
        print_error "虚拟环境不存在"
        return 1
    fi
    
    source .venv/bin/activate
    export ADMIN_DEFAULT_PASSWORD=testpass123
    
    if [ -f "reset_admin_user.py" ]; then
        python reset_admin_user.py > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            print_success "测试用户已创建/修复"
            return 0
        else
            print_error "创建用户失败"
            return 1
        fi
    else
        print_error "reset_admin_user.py 不存在"
        return 1
    fi
}

# 函数：启动后端服务（如果需要）
start_backend() {
    print_info "尝试启动后端服务..."
    # 这里只是提示，因为启动后端需要特定环境
    print_info "请手动启动后端服务："
    print_info "  cd ~/liaotian/admin-backend"
    print_info "  source .venv/bin/activate"
    print_info "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    return 1
}

# 函数：启动测试
start_test() {
    print_info "启动测试任务..."
    cd ~/liaotian/saas-demo
    
    if [ -f "启动后台测试.sh" ]; then
        chmod +x 启动后台测试.sh
        bash 启动后台测试.sh > /dev/null 2>&1
        sleep 2
        return 0
    else
        print_error "启动脚本不存在"
        return 1
    fi
}

# 函数：检查测试状态
check_test_status() {
    PID_FILE="$LOG_DIR/e2e_test.pid"
    
    if [ ! -f "$PID_FILE" ]; then
        return 1  # 没有运行中的测试
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        return 0  # 测试正在运行
    else
        return 2  # 测试已结束
    fi
}

# 函数：获取测试日志
get_test_log() {
    LATEST_LOG=$(ls -t "$LOG_DIR"/e2e_test_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "$LATEST_LOG"
        return 0
    else
        return 1
    fi
}

# 函数：检查错误
check_errors() {
    LOG_FILE=$(get_test_log)
    if [ -z "$LOG_FILE" ]; then
        return 0
    fi
    
    # 检查常见错误
    if grep -qi "错误\|error\|失败\|failed\|无法\|cannot" "$LOG_FILE" | tail -5; then
        return 1
    fi
    
    return 0
}

# 主循环
print_status "开始监控循环..."

MAX_ATTEMPTS=10
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    print_status "检查轮次: $ATTEMPT/$MAX_ATTEMPTS"
    
    # 检查后端服务
    if ! check_backend; then
        print_error "后端服务未运行"
        if ! start_backend; then
            print_info "等待后端服务启动..."
            sleep 5
            continue
        fi
    else
        print_success "后端服务运行正常"
    fi
    
    # 检查测试用户
    if ! check_test_user; then
        print_error "测试用户登录失败"
        if fix_test_user; then
            sleep 2
            if check_test_user; then
                print_success "测试用户已修复"
            else
                print_error "修复后仍然失败"
                continue
            fi
        else
            print_error "无法修复测试用户"
            continue
        fi
    else
        print_success "测试用户登录正常"
    fi
    
    # 检查测试状态
    TEST_STATUS=$(check_test_status)
    case $TEST_STATUS in
        0)
            print_info "测试正在运行中..."
            LOG_FILE=$(get_test_log)
            if [ -n "$LOG_FILE" ]; then
                print_info "最新日志: $LOG_FILE"
                echo "最后 5 行日志:"
                tail -5 "$LOG_FILE" 2>/dev/null | sed 's/^/  /'
            fi
            ;;
        1)
            print_info "没有运行中的测试，启动测试..."
            if start_test; then
                print_success "测试已启动"
                sleep 3
            else
                print_error "无法启动测试"
            fi
            ;;
        2)
            print_info "测试已结束，检查结果..."
            LOG_FILE=$(get_test_log)
            if [ -n "$LOG_FILE" ]; then
                print_info "测试日志: $LOG_FILE"
                echo ""
                echo "测试结果摘要:"
                echo "----------------------------------------"
                tail -30 "$LOG_FILE" | grep -E "成功|失败|通过|✅|❌|完成|错误" | tail -10
                echo "----------------------------------------"
                
                # 检查是否成功
                if tail -50 "$LOG_FILE" | grep -qi "所有测试通过\|测试完成.*成功"; then
                    print_success "测试成功完成！"
                    echo ""
                    echo "========================================"
                    echo "所有任务完成！"
                    echo "========================================"
                    exit 0
                elif tail -50 "$LOG_FILE" | grep -qi "测试失败\|错误"; then
                    print_error "测试失败，检查错误..."
                    echo ""
                    echo "错误详情:"
                    grep -i "error\|失败\|错误" "$LOG_FILE" | tail -10
                    exit 1
                else
                    print_info "测试已结束，状态未知"
                    exit 0
                fi
            else
                print_error "无法找到测试日志"
            fi
            break
            ;;
    esac
    
    # 等待一段时间后再次检查
    if [ $TEST_STATUS -eq 0 ]; then
        print_info "等待 10 秒后再次检查..."
        sleep 10
    else
        sleep 3
    fi
    
    echo ""
done

print_error "达到最大检查次数，监控结束"
exit 1
