# UPSERT 功能部署完成报告

## ✅ 部署状态

### 1. 代码修改
- ✅ **文件**: `admin-backend/app/api/group_ai/accounts.py`
- ✅ **修改位置**: 第1074-1137行
- ✅ **修改内容**: 将 `update_account` 函数改为 UPSERT 模式

### 2. 文件部署
- ✅ **服务器**: ubuntu@165.154.233.55
- ✅ **文件路径**: `~/liaotian/admin-backend/app/api/group_ai/accounts.py`
- ✅ **备份**: 已创建备份文件

### 3. 服务状态
- ✅ **后端服务**: 已重启
- ⚠️ **需要验证**: 服务是否正常运行

## 📝 修改说明

### 功能变化

**修改前**：
- 账号不存在时 → 返回 404 错误

**修改后（UPSERT）**：
- 账号不存在 + 提供 `server_id` → 创建新记录，返回 200/201
- 账号不存在 + 未提供 `server_id` → 返回 400 错误
- 账号已存在 → 正常更新，返回 200

### 关键代码

```python
if not db_account:
    # UPSERT 模式：账号不存在，根据请求创建新记录
    if not request.server_id:
        raise HTTPException(status_code=400, detail="創建新賬號時必須提供 server_id")
    
    # 创建新记录
    db_account = GroupAIAccount(
        account_id=account_id,
        session_file=session_file_path,
        script_id=request.script_id or "",
        server_id=request.server_id,
        # ... 其他字段
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
```

## 🧪 测试建议

### 快速测试命令

```bash
# 在服务器上执行
cd ~/liaotian/admin-backend
source .venv/bin/activate

# 登录获取token
TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123' | \
  python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

# 测试 UPSERT
curl -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"script_id": "test-script", "server_id": "computer_001"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -v
```

### 预期结果

- ✅ HTTP 状态码：200 或 201（不再是 404）
- ✅ 响应包含创建的账号对象
- ✅ 数据库中已创建新记录

## 🔧 后续步骤

1. **验证服务运行**：
   ```bash
   ssh ubuntu@165.154.233.55 "curl http://localhost:8000/health"
   ```

2. **检查后端日志**：
   ```bash
   ssh ubuntu@165.154.233.55 "tail -50 /tmp/backend.log"
   ```

3. **在浏览器中测试**：
   - 访问：http://aikz.usdt2026.cc/group-ai/accounts
   - 尝试"分配剧本"功能
   - 验证不再出现 404 错误

## ⚠️ 注意事项

1. 如果仍然返回 404，请检查：
   - 后端服务是否已重启
   - 文件是否已正确上传
   - 日志中是否有错误信息

2. 创建新账号时，必须提供 `server_id`，否则会返回 400 错误

---

**部署时间**: 2025-11-29  
**部署人员**: AI Assistant  
**状态**: ✅ 文件已部署，待验证
