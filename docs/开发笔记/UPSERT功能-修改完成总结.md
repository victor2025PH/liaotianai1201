# UPSERT功能 - 修改完成总结

## ✅ 修改完成

已成功将 `PUT /api/v1/group-ai/accounts/{account_id}` 接口改为 **UPSERT 模式**（存在则更新，不存在则创建）。

## 📝 修改内容

### 修改的文件

- `admin-backend/app/api/group_ai/accounts.py` - `update_account` 函数（第1041-1279行）

### 修改逻辑

**原来的行为**：
- 如果账号不存在（既不在 AccountManager 也不在数据库）→ 返回 404 错误

**新的行为（UPSERT）**：
1. 如果账号存在（在 AccountManager 或数据库中）→ **正常更新**
2. 如果账号不存在：
   - 如果提供了 `server_id` → **直接创建新记录**
   - 如果没有提供 `server_id` → 返回 400 错误（要求必须提供）

### 创建新记录时的字段处理

- `account_id`: 使用请求路径中的 account_id
- `session_file`: 请求中的值，或 `{account_id}.session`（默认）
- `script_id`: 请求中的值，或空字符串 `""`（默认）
- `server_id`: **必须提供**（如果没有则返回 400）
- `group_ids`: 请求中的值，或空数组 `[]`（默认）
- 其他字段：使用请求中的值或模型定义的默认值

## 🧪 测试命令

### 快速测试（在服务器上执行）

```bash
# 在远程服务器 ubuntu@165.154.233.55 上执行

# 1. 登录获取token
cd ~/liaotian/admin-backend
source .venv/bin/activate 2>/dev/null || true
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

### 完整测试脚本

使用已创建的测试脚本：

```bash
bash ~/liaotian/deploy/测试UPSERT功能.sh
```

## 📋 预期结果

### 第一次调用（账号不存在）

- **请求**: `PUT /api/v1/group-ai/accounts/639277358115`
- **请求体**: `{"script_id": "test-script", "server_id": "computer_001"}`
- **预期结果**: 
  - ✅ HTTP 状态码: **200** 或 **201**（不再是 404）
  - ✅ 返回创建的账号对象
  - ✅ 数据库中已创建新记录

### 第二次调用（账号已存在）

- **请求**: `PUT /api/v1/group-ai/accounts/639277358115`
- **请求体**: `{"script_id": "updated-script", "server_id": "computer_001"}`
- **预期结果**:
  - ✅ HTTP 状态码: **200**
  - ✅ 返回更新的账号对象
  - ✅ `script_id` 已更新为 `"updated-script"`

### 缺少 server_id 的情况

- **请求**: `PUT /api/v1/group-ai/accounts/test_account_999`
- **请求体**: `{"script_id": "test-script"}` （缺少 server_id）
- **预期结果**:
  - ✅ HTTP 状态码: **400**
  - ✅ 错误信息: "創建新賬號時必須提供 server_id"

## 🔧 在服务器上测试的完整命令

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

echo "Token: $TOKEN"
echo ""

# 2. 测试 UPSERT：创建新账号（账号不存在）
echo "【测试1】创建新账号 639277358115..."
curl -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id": "test-script", "server_id": "computer_001"}' \
  -w "\nHTTP状态码: %{http_code}\n" \
  -v 2>&1 | grep -E "HTTP|状态码|account_id|script_id" || echo ""

echo ""
echo "如果看到 HTTP 200 或 201，说明 UPSERT 功能正常！"
echo "如果看到 HTTP 404，说明修改还未生效，需要重启后端服务。"
```

## ⚠️ 重要提示

**修改代码后，需要重启后端服务才能生效**：

```bash
# 在服务器上执行
cd ~/liaotian/admin-backend
source .venv/bin/activate
pkill -f "uvicorn.*app.main:app" || true
sleep 2
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
sleep 5

# 验证后端已启动
curl http://localhost:8000/health
```

---

**修改完成时间**: 2025-11-29  
**修改文件**: `admin-backend/app/api/group_ai/accounts.py`
