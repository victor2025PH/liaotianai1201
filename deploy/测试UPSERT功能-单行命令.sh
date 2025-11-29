#!/bin/bash
# 测试 UPSERT 功能 - 单行命令版本
# 在远程服务器 ubuntu@165.154.233.55 上执行

cd ~/liaotian/admin-backend && source .venv/bin/activate 2>/dev/null || true && \
TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=admin@example.com&password=changeme123' | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])') && \
echo "=== 测试 UPSERT: 创建新账号（账号不存在）===" && \
curl -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id": "test-script", "server_id": "computer_001"}' \
  -v 2>&1 | head -30 && \
echo "" && \
echo "=== 如果返回 200/201 而不是 404，则 UPSERT 功能正常 ==="
