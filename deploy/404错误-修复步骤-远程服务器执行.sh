#!/bin/bash
# 404错误修复步骤 - 在远程服务器上执行
# 执行位置: ubuntu@165.154.233.55

echo "========================================="
echo "404错误修复 - 在远程服务器上执行"
echo "服务器: ubuntu@165.154.233.55"
echo "========================================="
echo ""

# 1. 强制重启后端服务
echo "【步骤1】强制重启后端服务..."
cd ~/liaotian/admin-backend || {
    echo "错误: 无法进入 ~/liaotian/admin-backend 目录"
    exit 1
}

source .venv/bin/activate || {
    echo "错误: 无法激活虚拟环境"
    exit 1
}

# 强制杀死所有uvicorn进程
echo "  正在停止旧的后端服务..."
pkill -9 -f 'uvicorn.*app.main:app' || echo "  没有找到运行中的后端服务"
sleep 3

# 重新启动（使用--reload参数）
echo "  正在启动后端服务（带自动重载）..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend_final.log 2>&1 &
BACKEND_PID=$!
sleep 5

# 验证服务启动
echo "  验证后端服务..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "  ✓ 后端服务已成功启动"
else
    echo "  ✗ 后端服务启动失败，请查看日志: tail -50 /tmp/backend_final.log"
    exit 1
fi
echo ""

# 2. 测试PUT请求
echo "【步骤2】测试PUT请求..."
echo "  登录获取token..."
LOGIN_RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')
    echo "  ✓ 登录成功"
else
    echo "  ✗ 登录失败: $LOGIN_RESPONSE"
    exit 1
fi

echo "  测试PUT请求..."
PUT_RESPONSE=$(curl -s -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id":"test-script","server_id":"computer_001"}')

PUT_STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id":"test-script","server_id":"computer_001"}')

echo "  PUT请求状态码: $PUT_STATUS"
echo "  PUT请求响应: ${PUT_RESPONSE:0:200}..."
echo ""

# 3. 查看日志
echo "【步骤3】查看后端日志（最近50行，包含UPDATE_ACCOUNT等关键词）..."
echo "  日志内容:"
tail -50 /tmp/backend_final.log | grep -E "UPDATE_ACCOUNT|MIDDLEWARE|PUT|404|639277358115" | tail -20 || echo "  未找到相关日志"

echo ""
echo "========================================="
echo "修复步骤执行完成"
echo "========================================="
echo ""
echo "如果仍然有问题，请："
echo "1. 查看完整日志: tail -100 /tmp/backend_final.log"
echo "2. 实时监控日志: tail -f /tmp/backend_final.log | grep -E 'UPDATE_ACCOUNT|PUT|404'"
echo "3. 检查后端服务状态: ps aux | grep uvicorn"
