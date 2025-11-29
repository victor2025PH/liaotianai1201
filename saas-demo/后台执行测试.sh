#!/bin/bash
# 后台执行测试脚本 - 将输出保存到日志文件

# 设置日志文件路径
LOG_DIR="$HOME/liaotian/test_logs"
LOG_FILE="$LOG_DIR/e2e_test_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="$LOG_DIR/e2e_test.pid"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查是否已有测试在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "警告: 已有测试进程在运行 (PID: $OLD_PID)"
        echo "如需停止: kill $OLD_PID"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# 保存当前进程 PID
echo $$ > "$PID_FILE"

# 重定向所有输出到日志文件
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "========================================"
echo "E2E 测试后台执行开始"
echo "========================================"
echo "进程 ID: $$"
echo "日志文件: $LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 颜色输出（虽然会保存到文件，但保留以便查看时使用）
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[步骤 $1/$2]${NC} $3 - $(date '+%H:%M:%S')"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# 步骤 1: 创建测试用户
print_step "1" "5" "创建/重置测试用户"
cd ~/liaotian/admin-backend || {
    print_error "无法进入 admin-backend 目录"
    exit 1
}

if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    print_error "虚拟环境不存在"
    exit 1
fi

export ADMIN_DEFAULT_PASSWORD=testpass123

if [ -f "reset_admin_user.py" ]; then
    python reset_admin_user.py || {
        print_error "创建用户失败"
        exit 1
    }
    print_success "测试用户已创建/重置"
else
    print_error "reset_admin_user.py 不存在"
    exit 1
fi

echo ""

# 步骤 2: 验证登录
print_step "2" "5" "验证登录端点"
sleep 2

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    print_success "登录验证成功"
else
    print_error "登录验证失败"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi

echo ""

# 步骤 3: 检查后端服务
print_step "3" "5" "检查后端服务状态"

if curl -s http://localhost:8000/health > /dev/null; then
    HEALTH=$(curl -s http://localhost:8000/health)
    print_success "后端服务正在运行: $HEALTH"
else
    print_error "后端服务未运行"
    exit 1
fi

echo ""

# 步骤 4: 安装 Playwright 浏览器
print_step "4" "5" "安装 Playwright 浏览器"

cd ~/liaotian/saas-demo || {
    print_error "无法进入 saas-demo 目录"
    exit 1
}

if [ ! -d "node_modules/@playwright" ]; then
    print_error "Playwright 未安装，请先运行: npm install"
    exit 1
fi

echo "正在安装 Chromium 浏览器..."
if npx playwright install chromium --with-deps 2>/dev/null; then
    print_success "浏览器已安装（含系统依赖）"
elif npx playwright install chromium 2>/dev/null; then
    print_success "浏览器已安装"
else
    print_error "浏览器安装失败"
    exit 1
fi

echo ""

# 步骤 5: 运行测试
print_step "5" "5" "运行 E2E 测试"

echo ""
echo "========================================"
echo "开始运行 E2E 测试"
echo "========================================"
echo ""

# 运行测试
npm run test:e2e
TEST_EXIT_CODE=$?

echo ""
echo "========================================"
echo "测试执行完成 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "所有测试通过！"
else
    print_error "测试失败，退出码: $TEST_EXIT_CODE"
fi

# 清理 PID 文件
rm -f "$PID_FILE"

exit $TEST_EXIT_CODE
