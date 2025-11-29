#!/bin/bash
# 服务器自动测试脚本 - 全自动执行 E2E 测试准备和运行

set -e  # 遇到错误立即退出

echo "========================================"
echo "E2E 测试自动化脚本"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 步骤 1: 创建/重置测试用户
echo -e "${YELLOW}[1/4] 创建/重置测试用户...${NC}"
cd ~/liaotian/admin-backend

# 检查虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo -e "${RED}❌ 虚拟环境不存在${NC}"
    exit 1
fi

# 设置环境变量
export ADMIN_DEFAULT_PASSWORD=testpass123

# 运行重置脚本
if [ -f "reset_admin_user.py" ]; then
    python reset_admin_user.py
    echo -e "${GREEN}✅ 测试用户已创建/重置${NC}"
else
    echo -e "${RED}❌ reset_admin_user.py 不存在${NC}"
    exit 1
fi

echo ""

# 步骤 2: 验证登录
echo -e "${YELLOW}[2/4] 验证登录端点...${NC}"
sleep 2  # 等待数据库操作完成

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ 登录成功${NC}"
    echo "响应: $(echo $LOGIN_RESPONSE | cut -c1-50)..."
else
    echo -e "${RED}❌ 登录失败${NC}"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi

echo ""

# 步骤 3: 安装 Playwright 浏览器
echo -e "${YELLOW}[3/4] 安装 Playwright 浏览器...${NC}"
cd ~/liaotian/saas-demo

# 检查是否已安装
if [ -d "node_modules/@playwright" ]; then
    echo "✅ Playwright 已安装"
else
    echo "正在安装 Playwright..."
    npm install
fi

# 安装浏览器
echo "正在安装 Chromium 浏览器..."
npx playwright install chromium --with-deps || npx playwright install chromium
echo -e "${GREEN}✅ 浏览器已安装${NC}"

echo ""

# 步骤 4: 运行 E2E 测试
echo -e "${YELLOW}[4/4] 运行 E2E 测试...${NC}"
echo ""

# 检查后端服务是否运行
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务正在运行"
else
    echo -e "${RED}❌ 后端服务未运行，请先启动后端服务${NC}"
    echo "启动命令: cd ~/liaotian/admin-backend && source .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

# 运行测试
echo "开始运行测试..."
npm run test:e2e

echo ""
echo -e "${GREEN}========================================"
echo "测试完成！"
echo "========================================${NC}"
