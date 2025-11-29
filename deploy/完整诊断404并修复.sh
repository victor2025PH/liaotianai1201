#!/bin/bash
set -e

cd ~/liaotian

echo "========================================="
echo "完整诊断并修复404错误"
echo "========================================="
echo ""

# 1. 检查并启动后端服务
echo "【1】检查后端服务..."
if ! ps aux | grep -v grep | grep "uvicorn.*app.main:app" > /dev/null; then
    echo "  ✗ 后端服务未运行，正在启动..."
    cd admin-backend
    source .venv/bin/activate
    pkill -f 'uvicorn.*app.main:app' || true
    sleep 2
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
    sleep 5
    cd ..
else
    echo "  ✓ 后端服务正在运行"
fi

# 2. 验证后端健康
echo ""
echo "【2】验证后端健康..."
if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok"; then
    echo "  ✓ 后端健康检查通过"
else
    echo "  ✗ 后端健康检查失败，重新启动..."
    cd admin-backend
    source .venv/bin/activate
    pkill -f 'uvicorn.*app.main:app' || true
    sleep 2
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_final.log 2>&1 &
    sleep 5
    cd ..
fi

# 3. 登录并测试PUT请求
echo ""
echo "【3】测试完整的PUT请求流程..."
cd admin-backend
source .venv/bin/activate

python3 << 'PYTHON_SCRIPT'
import requests
import json
import sys

# 登录
login_url = 'http://localhost:8000/api/v1/auth/login'
login_res = requests.post(login_url, data={
    'username': 'admin@example.com',
    'password': 'changeme123'
}, timeout=5)

if login_res.status_code != 200:
    print(f"  ✗ 登录失败: {login_res.status_code}")
    print(f"  响应: {login_res.text[:200]}")
    sys.exit(1)

token = login_res.json()['access_token']
print(f"  ✓ 登录成功")

# 测试PUT请求
put_url = 'http://localhost:8000/api/v1/group-ai/accounts/639277358115'
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
data = {
    'script_id': 'test-script-id',
    'server_id': 'computer_001'
}

print(f"  测试 PUT {put_url}")
print(f"  请求数据: {json.dumps(data)}")

response = requests.put(put_url, json=data, headers=headers, timeout=10)

print(f"  响应状态码: {response.status_code}")
print(f"  响应内容: {response.text[:500]}")

if response.status_code == 404:
    print(f"  ✗ 收到404错误")
    print(f"  错误详情: {response.text[:300]}")
else:
    print(f"  ✓ 请求成功")
PYTHON_SCRIPT

cd ..

# 4. 查看日志
echo ""
echo "【4】查看后端日志（最后30行）..."
if [ -f /tmp/backend_final.log ]; then
    echo "  日志文件存在，查看最后30行:"
    tail -30 /tmp/backend_final.log | grep -E "UPDATE_ACCOUNT|PUT|404|639277358115|ERROR|Exception" | tail -15 || echo "  未找到相关日志"
else
    echo "  ✗ 日志文件不存在"
fi

echo ""
echo "========================================="
echo "诊断完成"
echo "========================================="
