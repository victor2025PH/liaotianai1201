#!/bin/bash
# 主控脚本：自动执行所有步骤并监控直到完成

set -e

LOG_DIR="$HOME/liaotian/test_logs"
mkdir -p "$LOG_DIR"
MAIN_LOG="$LOG_DIR/main_execution_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$MAIN_LOG")
exec 2>&1

echo "========================================"
echo "主控自动执行和监控系统"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1"; }
info() { echo -e "${BLUE}ℹ️${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; }

# 步骤 1: 确保后端服务运行
info "步骤 1: 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    success "后端服务正在运行"
else
    error "后端服务未运行"
    warn "请先启动后端服务，然后重新运行此脚本"
    exit 1
fi

# 步骤 2: 创建/修复测试用户
info "步骤 2: 创建/修复测试用户..."
cd ~/liaotian/admin-backend

if [ ! -d ".venv" ]; then
    error "虚拟环境不存在"
    exit 1
fi

source .venv/bin/activate
export ADMIN_DEFAULT_PASSWORD=testpass123

if [ -f "reset_admin_user.py" ]; then
    if python reset_admin_user.py > /dev/null 2>&1; then
        success "测试用户已创建/修复"
    else
        error "创建用户失败"
        exit 1
    fi
else
    error "reset_admin_user.py 不存在"
    exit 1
fi

sleep 2

# 步骤 3: 验证登录
info "步骤 3: 验证登录..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    success "登录验证成功"
else
    error "登录验证失败"
    echo "响应: ${LOGIN_RESPONSE:0:200}"
    exit 1
fi

# 步骤 4: 确保脚本就绪
info "步骤 4: 准备测试脚本..."
cd ~/liaotian/saas-demo

# 拉取最新代码
if git pull origin master > /dev/null 2>&1; then
    success "代码已更新"
fi

# 确保脚本可执行
chmod +x 启动后台测试.sh 查看测试日志.sh 后台执行测试.sh 检查测试状态.sh 2>/dev/null || true

# 步骤 5: 启动测试
info "步骤 5: 启动测试任务..."

# 检查是否已有测试在运行
PID_FILE="$LOG_DIR/e2e_test.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        warn "已有测试在运行 (PID: $OLD_PID)，跳过启动"
    else
        rm -f "$PID_FILE"
        info "启动新的测试任务..."
        bash 启动后台测试.sh > /dev/null 2>&1 &
        sleep 3
    fi
else
    info "启动新的测试任务..."
    bash 启动后台测试.sh > /dev/null 2>&1 &
    sleep 3
fi

# 步骤 6: 持续监控
info "步骤 6: 开始监控测试进度..."
echo ""

MAX_WAIT=1800  # 最多等待30分钟
WAIT_TIME=0
CHECK_INTERVAL=10

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    # 检查测试状态
    cd ~/liaotian/saas-demo
    
    STATUS_OUTPUT=$(bash 检查测试状态.sh 2>&1)
    EXIT_CODE=$?
    
    echo "[$(date '+%H:%M:%S')] 状态检查:"
    echo "$STATUS_OUTPUT"
    echo ""
    
    case $EXIT_CODE in
        0)
            success "测试成功完成！"
            echo ""
            echo "========================================"
            echo "所有任务已完成！"
            echo "========================================"
            exit 0
            ;;
        1)
            error "测试失败或有错误"
            echo ""
            
            # 尝试修复
            info "尝试修复问题..."
            
            # 检查并修复测试用户
            if ! echo "$STATUS_OUTPUT" | grep -q "测试用户登录成功"; then
                info "修复测试用户..."
                cd ~/liaotian/admin-backend
                source .venv/bin/activate
                export ADMIN_DEFAULT_PASSWORD=testpass123
                python reset_admin_user.py > /dev/null 2>&1
                sleep 2
            fi
            
            # 重新启动测试
            info "重新启动测试..."
            cd ~/liaotian/saas-demo
            rm -f "$LOG_DIR/e2e_test.pid"
            bash 启动后台测试.sh > /dev/null 2>&1 &
            sleep 5
            ;;
        2)
            info "测试仍在进行中，继续监控..."
            ;;
    esac
    
    sleep $CHECK_INTERVAL
    WAIT_TIME=$((WAIT_TIME + CHECK_INTERVAL))
done

error "达到最大等待时间，监控结束"
exit 1
