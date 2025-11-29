# UPSERT 功能 - 测试命令

## 修改说明

已将 `PUT /api/v1/group-ai/accounts/{account_id}` 接口改为 **UPSERT 模式**（存在则更新，不存在则创建）。

## 快速测试命令

### 在服务器上执行以下命令进行测试

```bash
# 在远程服务器 ubuntu@165.154.233.55 上执行

# 1. 登录获取token
TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123' | \
  python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

# 2. 测试 UPSERT：创建新账号（账号不存在）
curl -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script",
    "server_id": "computer_001"
  }' \
  -v

# 预期结果：返回 HTTP 200 或 201，不再是 404
```

## 完整测试脚本

使用以下脚本进行完整测试：

```bash
bash ~/liaotian/deploy/测试UPSERT功能.sh
```

或直接在服务器上执行：

```bash
#!/bin/bash
# 在远程服务器 ubuntu@165.154.233.55 上执行

cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true

# 1. 登录获取token
TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123' | \
  python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

echo "测试 UPSERT 功能..."
echo ""

# 2. 测试创建新账号（账号不存在）
echo "【测试1】创建新账号 639277358115..."
STATUS_CODE=$(curl -s -o /tmp/upsert_response.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id": "test-script", "server_id": "computer_001"}')

echo "HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "201" ]; then
    echo "✓ 成功！不再返回 404"
    cat /tmp/upsert_response.json | python3 -m json.tool | head -20
else
    echo "✗ 失败，状态码: $STATUS_CODE"
    cat /tmp/upsert_response.json
fi
echo ""

# 3. 测试更新已存在的账号
echo "【测试2】更新已存在的账号..."
STATUS_CODE=$(curl -s -o /tmp/upsert_update.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id": "updated-script", "server_id": "computer_001"}')

echo "HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "200" ]; then
    echo "✓ 更新成功"
else
    echo "✗ 更新失败"
    cat /tmp/upsert_update.json
fi
echo ""

echo "测试完成！"
```

## 预期结果

### 第一次调用（账号不存在）

- **HTTP 状态码**: 200 或 201（不再是 404）
- **响应**: 包含创建的账号对象
- **数据库**: 新记录已创建

### 第二次调用（账号已存在）

- **HTTP 状态码**: 200
- **响应**: 包含更新后的账号对象
- **字段**: script_id 等字段已更新

---

**重要**: 确保后端服务已重启以加载新的代码修改！
