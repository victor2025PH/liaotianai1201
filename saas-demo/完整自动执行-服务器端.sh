#!/bin/bash
# 完整自动执行脚本 - 在服务器上直接运行
# 使用方法: bash 完整自动执行-服务器端.sh

set -e

LOG_DIR="$HOME/liaotian/test_logs"
mkdir -p "$LOG_DIR"
EXEC_LOG="$LOG_DIR/complete_execution_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$EXEC_LOG")
exec 2>&1

echo "========================================"
echo "完整自动执行脚本"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "日志文件: $EXEC_LOG"
echo "========================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1"; }
info() { echo -e "${BLUE}ℹ️${NC} $1"; }
step() { echo -e "${YELLOW}[步骤]${NC} $1"; }

# 步骤 1: 更新代码
step "1. 更新代码"
cd ~/liaotian/saas-demo
git pull origin master
success "代码已更新"
echo ""

# 步骤 2: 检查后端服务
step "2. 检查后端服务"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    success "后端服务运行正常"
else
    error "后端服务未运行"
    info "请先启动后端服务"
    exit 1
fi
echo ""

# 步骤 3: 创建测试用户
step "3. 创建/修复测试用户"
cd ~/liaotian/admin-backend
source .venv/bin/activate
export ADMIN_DEFAULT_PASSWORD=testpass123
python reset_admin_user.py
success "测试用户已创建"
sleep 2
echo ""

# 步骤 4: 验证登录
step "4. 验证登录"
LOGIN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123")

if echo "$LOGIN" | grep -q "access_token"; then
    success "登录验证成功"
else
    error "登录验证失败"
    exit 1
fi
echo ""

# 步骤 5: 安装浏览器
step "5. 安装 Playwright 浏览器"
cd ~/liaotian/saas-demo
npx playwright install chromium
success "浏览器已安装"
echo ""

# 步骤 6: 运行测试
step "6. 运行 E2E 测试"
echo ""
echo "========================================"
echo "开始运行测试..."
echo "========================================"
echo ""

npm run test:e2e
TEST_EXIT=$?

echo ""
echo "========================================"
if [ $TEST_EXIT -eq 0 ]; then
    success "所有任务完成！测试通过！"
else
    error "测试失败，退出码: $TEST_EXIT"
fi
echo "========================================"
echo ""
echo "执行日志: $EXEC_LOG"

exit $TEST_EXIT
