# UPSERT功能 - 更新账号接口修改

## 修改说明

已将 `PUT /api/v1/group-ai/accounts/{account_id}` 接口改为 **UPSERT 模式**（存在则更新，不存在则创建）。

## 修改内容

### 修改的文件

- `admin-backend/app/api/group_ai/accounts.py` - `update_account` 函数

### 修改逻辑

**原来的逻辑**：
- 如果账号不存在（既不在 AccountManager 也不在数据库），返回 404 错误

**新的逻辑（UPSERT）**：
1. 如果账号存在（在 AccountManager 或数据库中）→ 正常更新
2. 如果账号不存在：
   - 如果提供了 `server_id` → 直接创建新记录
   - 如果没有提供 `server_id` → 返回 400 错误（要求必须提供）
   - 尝试扫描远程服务器获取更多信息（可选，不阻塞创建）

### 创建新记录时的默认值

- `account_id`: 使用请求中的 account_id
- `session_file`: 使用请求中的 session_file，否则使用 `{account_id}.session`
- `script_id`: 使用请求中的 script_id，否则使用空字符串 `""`
- `server_id`: **必须提供**（如果没有则返回 400）
- `group_ids`: 使用请求中的 group_ids，否则使用空数组 `[]`
- `active`: 使用请求中的 active，否则默认为 `True`
- `reply_rate`: 使用请求中的 reply_rate，否则默认为 `0.3`
- `redpacket_enabled`: 使用请求中的 redpacket_enabled，否则默认为 `True`
- `redpacket_probability`: 使用请求中的 redpacket_probability，否则默认为 `0.5`
- `max_replies_per_hour`: 使用请求中的 max_replies_per_hour，否则默认为 `50`
- `min_reply_interval`: 使用请求中的 min_reply_interval，否则默认为 `3`

## 测试命令

### 1. 测试创建新账号（账号不存在）

```bash
# 在服务器上执行
# 先登录获取token
TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123' | \
  python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

# 测试 UPSERT：创建新账号（如果不存在）
curl -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script",
    "server_id": "computer_001"
  }' \
  -v

# 应该返回 200 或 201，而不是 404
```

### 2. 测试更新已存在的账号

```bash
# 再次调用相同的 PUT 请求，应该更新而不是创建
curl -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "updated-script",
    "server_id": "computer_001"
  }' \
  -v

# 应该返回 200，且 script_id 已更新
```

### 3. 验证账号是否已创建

```bash
# 获取账号列表，确认账号已存在
curl -s "http://localhost:8000/api/v1/group-ai/accounts?page=1&page_size=100" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c 'import sys, json; accounts=json.load(sys.stdin); print([acc["account_id"] for acc in accounts if acc["account_id"] == "639277358115"])'
```

### 4. 测试缺少 server_id 的情况

```bash
# 测试不提供 server_id（应该返回 400）
curl -X PUT "http://localhost:8000/api/v1/group-ai/accounts/test_account_999" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script"
  }' \
  -v

# 应该返回 400 Bad Request，提示需要提供 server_id
```

## 完整测试脚本

在服务器上执行以下脚本进行完整测试：

```bash
#!/bin/bash
# 在远程服务器 ubuntu@165.154.233.55 上执行

# 1. 登录获取token
echo "【步骤1】登录获取token..."
TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123' | \
  python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

if [ -z "$TOKEN" ]; then
    echo "✗ 登录失败"
    exit 1
fi
echo "✓ 登录成功"
echo ""

# 2. 测试 UPSERT：创建新账号（账号不存在）
echo "【步骤2】测试 UPSERT - 创建新账号..."
TEST_ACCOUNT_ID="639277358115"
STATUS_CODE=$(curl -s -o /tmp/upsert_response.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script",
    "server_id": "computer_001"
  }')

echo "HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "201" ]; then
    echo "✓ UPSERT 成功（创建新账号）"
    cat /tmp/upsert_response.json | python3 -m json.tool
else
    echo "✗ UPSERT 失败"
    cat /tmp/upsert_response.json
fi
echo ""

# 3. 验证账号已创建
echo "【步骤3】验证账号是否已创建..."
ACCOUNT_EXISTS=$(curl -s "http://localhost:8000/api/v1/group-ai/accounts?page=1&page_size=100" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys, json; accounts=json.load(sys.stdin); print('YES' if any(acc.get('account_id') == '$TEST_ACCOUNT_ID' for acc in accounts) else 'NO')")

if [ "$ACCOUNT_EXISTS" = "YES" ]; then
    echo "✓ 账号 $TEST_ACCOUNT_ID 已存在于数据库中"
else
    echo "✗ 账号 $TEST_ACCOUNT_ID 未找到"
fi
echo ""

# 4. 测试更新已存在的账号
echo "【步骤4】测试 UPSERT - 更新已存在的账号..."
STATUS_CODE=$(curl -s -o /tmp/upsert_update_response.json -w '%{http_code}' -X PUT \
  "http://localhost:8000/api/v1/group-ai/accounts/$TEST_ACCOUNT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "updated-script",
    "server_id": "computer_001"
  }')

echo "HTTP 状态码: $STATUS_CODE"
if [ "$STATUS_CODE" = "200" ]; then
    echo "✓ UPSERT 成功（更新已存在的账号）"
    cat /tmp/upsert_update_response.json | python3 -m json.tool
else
    echo "✗ 更新失败"
    cat /tmp/upsert_update_response.json
fi
echo ""

echo "========================================="
echo "测试完成！"
echo "========================================="
```

## 预期结果

### 第一次调用（账号不存在）

- **请求**: `PUT /api/v1/group-ai/accounts/639277358115`
- **请求体**: `{"script_id": "test-script", "server_id": "computer_001"}`
- **预期结果**: 
  - HTTP 状态码: **200** 或 **201**
  - 返回创建的账号对象
  - 数据库中已创建新记录

### 第二次调用（账号已存在）

- **请求**: `PUT /api/v1/group-ai/accounts/639277358115`
- **请求体**: `{"script_id": "updated-script", "server_id": "computer_001"}`
- **预期结果**:
  - HTTP 状态码: **200**
  - 返回更新的账号对象
  - `script_id` 已更新为 `"updated-script"`

### 缺少 server_id 的情况

- **请求**: `PUT /api/v1/group-ai/accounts/test_account_999`
- **请求体**: `{"script_id": "test-script"}`
- **预期结果**:
  - HTTP 状态码: **400**
  - 错误信息: "创建新賬號時必須提供 server_id"

---

**修改完成时间**: 2025-11-29
**修改文件**: `admin-backend/app/api/group_ai/accounts.py`
