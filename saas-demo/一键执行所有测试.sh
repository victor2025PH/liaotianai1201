#!/bin/bash
# 一键执行所有测试 - 全自动化脚本
# 使用方法: bash 一键执行所有测试.sh

set -e  # 遇到错误立即退出

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_step() {
    echo -e "${BLUE}[步骤 $1/$2]${NC} $3"
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

# 主标题
echo ""
echo "========================================"
echo -e "${BLUE}E2E 测试全自动执行脚本${NC}"
echo "========================================"
echo ""

# 步骤 1: 创建/重置测试用户
print_step "1" "5" "创建/重置测试用户"

cd ~/liaotian/admin-backend || {
    print_error "无法进入 admin-backend 目录"
    exit 1
}

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
    print_info "虚拟环境已激活"
else
    print_error "虚拟环境不存在 (.venv)"
    exit 1
fi

# 检查重置脚本是否存在
if [ ! -f "reset_admin_user.py" ]; then
    print_error "reset_admin_user.py 不存在"
    exit 1
fi

# 设置环境变量并执行
export ADMIN_DEFAULT_PASSWORD=testpass123
print_info "使用密码: testpass123"

python reset_admin_user.py || {
    print_error "创建用户失败"
    exit 1
}

print_success "测试用户已创建/重置"
echo ""

# 步骤 2: 验证登录
print_step "2" "5" "验证登录端点"

sleep 2  # 等待数据库操作完成

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    print_success "登录验证成功"
    TOKEN_PREVIEW=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4 | cut -c1-20)
    print_info "Token 预览: ${TOKEN_PREVIEW}..."
else
    print_error "登录验证失败"
    print_info "响应: $LOGIN_RESPONSE"
    exit 1
fi

echo ""

# 步骤 3: 检查后端服务
print_step "3" "5" "检查后端服务状态"

if curl -s http://localhost:8000/health > /dev/null; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    print_success "后端服务正在运行"
    print_info "健康检查响应: $HEALTH_RESPONSE"
else
    print_error "后端服务未运行或无法访问"
    print_info "请先启动后端服务:"
    print_info "  cd ~/liaotian/admin-backend"
    print_info "  source .venv/bin/activate"
    print_info "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi

echo ""

# 步骤 4: 安装 Playwright 浏览器
print_step "4" "5" "安装 Playwright 浏览器"

cd ~/liaotian/saas-demo || {
    print_error "无法进入 saas-demo 目录"
    exit 1
}

# 检查 Playwright 是否已安装
if [ ! -d "node_modules/@playwright" ]; then
    print_info "Playwright 未安装，正在安装..."
    npm install --silent || {
        print_error "npm install 失败"
        exit 1
    }
    print_success "Playwright 已安装"
else
    print_info "Playwright 已安装，跳过 npm install"
fi

# 安装浏览器
print_info "正在安装 Chromium 浏览器（可能需要几分钟）..."

if npx playwright install chromium --with-deps 2>/dev/null; then
    print_success "Chromium 浏览器已安装（包含系统依赖）"
elif npx playwright install chromium 2>/dev/null; then
    print_success "Chromium 浏览器已安装"
else
    print_error "浏览器安装失败"
    exit 1
fi

echo ""

# 步骤 5: 运行 E2E 测试
print_step "5" "5" "运行 E2E 测试"

echo ""
echo "========================================"
echo -e "${BLUE}开始运行 E2E 测试${NC}"
echo "========================================"
echo ""
print_info "测试将自动启动前端服务"
print_info "后端服务应该已经运行在 http://localhost:8000"
echo ""

# 运行测试
npm run test:e2e || {
    print_error "测试执行失败"
    exit 1
}

echo ""
echo "========================================"
echo -e "${GREEN}✅ 所有操作完成！${NC}"
echo "========================================"
echo ""
