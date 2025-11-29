# UPSERT功能 - 修改总结和测试命令

## ✅ 修改完成

已成功将 `PUT /api/v1/group-ai/accounts/{account_id}` 接口改为 **UPSERT 模式**（存在则更新，不存在则创建）。

## 📝 修改内容

### 修改的文件

- `admin-backend/app/api/group_ai/accounts.py` - `update_account` 函数（第1074-1137行）

### 核心修改逻辑

**修改位置**：第1074-1137行

**原来的逻辑**：
```python
if not db_account:
    # 账号不存在，返回 404
    raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
```

**新的逻辑（UPSERT）**：
```python
if not db_account:
    # UPSERT 模式：如果账号不存在，直接创建新记录
    # 1. 检查是否提供了 server_id（必须）
    if not request.server_id:
        raise HTTPException(status_code=400, detail="创建新賬號時必須提供 server_id")
    
    # 2. 尝试扫描远程服务器获取信息（可选）
    # 3. 使用请求字段和默认值创建新记录
    db_account = GroupAIAccount(
        account_id=account_id,
        session_file=session_file_path,
        script_id=request.script_id or "",
        server_id=request.server_id,  # 必须提供
        # ... 其他字段使用请求值或默认值
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    # 继续更新逻辑...
```

### 关键改进

1. ✅ **不再返回 404**：账号不存在时，如果提供了 `server_id`，直接创建新记录
2. ✅ **必须提供 server_id**：创建新账号时，如果没有 `server_id`，返回 400 而不是 404
3. ✅ **可选扫描**：尝试扫描远程服务器获取更多信息，但不阻塞创建
4. ✅ **默认值处理**：所有字段都有合理的默认值

## 🧪 测试命令

### 在服务器上执行测试

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
  -w "\n\nHTTP状态码: %{http_code}\n" \
  -v

# 预期结果：
# - HTTP状态码: 200 或 201（不再是 404）
# - 返回创建的账号对象
```

### 使用测试脚本

```bash
# 在服务器上执行
bash ~/liaotian/deploy/测试UPSERT功能.sh
```

## 📊 预期结果对比

| 场景 | 原来行为 | 新行为（UPSERT） |
|------|---------|----------------|
| 账号不存在，提供 server_id | ❌ 返回 404 | ✅ 创建新记录，返回 200/201 |
| 账号不存在，未提供 server_id | ❌ 返回 404 | ⚠️ 返回 400（要求提供 server_id） |
| 账号已存在 | ✅ 返回 200，更新记录 | ✅ 返回 200，更新记录 |

## 🔧 重启后端服务

**修改代码后，必须重启后端服务才能生效**：

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
**修改行数**: 第1074-1137行
