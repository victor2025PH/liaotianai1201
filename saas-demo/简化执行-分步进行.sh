#!/bin/bash
# 简化执行脚本 - 分步执行便于调试

set -e

echo "========================================"
echo "简化分步执行脚本"
echo "========================================"
echo ""

# 步骤 1: 准备
echo "[步骤 1] 准备环境"
cd ~/liaotian/saas-demo
git pull origin master
chmod +x *.sh 2>/dev/null || true
echo "✅ 完成"
echo ""

# 步骤 2: 检查后端
echo "[步骤 2] 检查后端服务"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务未运行"
    exit 1
fi
echo ""

# 步骤 3: 创建用户
echo "[步骤 3] 创建测试用户"
cd ~/liaotian/admin-backend
source .venv/bin/activate
export ADMIN_DEFAULT_PASSWORD=testpass123
python reset_admin_user.py
echo "✅ 完成"
sleep 2
echo ""

# 步骤 4: 验证登录
echo "[步骤 4] 验证登录"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=testpass123")

if echo "$RESPONSE" | grep -q "access_token"; then
    echo "✅ 登录成功"
else
    echo "❌ 登录失败: ${RESPONSE:0:100}"
    exit 1
fi
echo ""

# 步骤 5: 安装浏览器
echo "[步骤 5] 安装浏览器"
cd ~/liaotian/saas-demo
npx playwright install chromium
echo "✅ 完成"
echo ""

# 步骤 6: 运行测试
echo "[步骤 6] 运行测试"
echo ""
npm run test:e2e
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 所有测试通过！"
else
    echo "❌ 测试失败，退出码: $EXIT_CODE"
fi

exit $EXIT_CODE
