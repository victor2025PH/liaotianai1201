#!/bin/bash
# 诊断404错误

cd ~/liaotian/admin-backend

echo "========================================="
echo "诊断404错误"
echo "========================================="
echo ""

source .venv/bin/activate

# 1. 检查后端服务
echo "【1】检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务正常运行"
else
    echo "  ✗ 后端服务未运行"
    exit 1
fi
echo ""

# 2. 测试路由
echo "【2】测试PUT路由..."
python3 << 'TESTROUTE'
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 测试路由
print("测试 PUT /api/v1/group-ai/accounts/test-id")
response = client.put(
    '/api/v1/group-ai/accounts/test-id',
    json={'script_id': 'test'},
    headers={'Authorization': 'Bearer invalid-token'}
)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:300]}")
print("")

# 列出所有PUT accounts路由
print("所有PUT accounts路由:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        if 'PUT' in route.methods and 'account' in route.path.lower():
            print(f"  PUT {route.path}")
TESTROUTE

echo ""
echo "【3】检查数据库中的账号..."
python3 << 'CHECKDB'
from app.db import get_db
from app.models.group_ai import GroupAIAccount

db = next(get_db())
account_id = '639277358115'

account = db.query(GroupAIAccount).filter(
    GroupAIAccount.account_id == account_id
).first()

if account:
    print(f"  ✓ 账号存在于数据库")
    print(f"  server_id: {account.server_id}")
    print(f"  script_id: {account.script_id or '未分配'}")
else:
    print(f"  ✗ 账号不存在于数据库")
CHECKDB

echo ""
echo "========================================="
echo "诊断完成"
echo "========================================="
