#!/bin/bash
# 完整执行命令 - 直接在服务器上复制粘贴执行

set -e

echo "========================================"
echo "开始自动执行 E2E 测试准备和运行"
echo "========================================"
echo ""

# 步骤 1: 创建测试用户
echo "[1/4] 创建/重置测试用户..."
cd ~/liaotian/admin-backend
source .venv/bin/activate
export ADMIN_DEFAULT_PASSWORD=testpass123
python reset_admin_user.py
echo "✅ 测试用户已创建"
echo ""

# 步骤 2: 验证登录
echo "[2/4] 验证登录..."
sleep 2
LOGIN_TEST=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123")

if echo "$LOGIN_TEST" | grep -q "access_token"; then
    echo "✅ 登录验证成功"
else
    echo "❌ 登录验证失败: $LOGIN_TEST"
    exit 1
fi
echo ""

# 步骤 3: 安装浏览器
echo "[3/4] 安装 Playwright 浏览器..."
cd ~/liaotian/saas-demo
npx playwright install chromium
echo "✅ 浏览器已安装"
echo ""

# 步骤 4: 检查后端服务
echo "[4/4] 检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务正在运行"
else
    echo "❌ 后端服务未运行，请先启动后端服务"
    exit 1
fi
echo ""

# 运行测试
echo "========================================"
echo "开始运行 E2E 测试"
echo "========================================"
npm run test:e2e

echo ""
echo "========================================"
echo "测试执行完成！"
echo "========================================"
