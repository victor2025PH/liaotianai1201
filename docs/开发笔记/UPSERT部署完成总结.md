# UPSERT 功能部署完成总结

## ✅ 已完成的工作

### 1. 代码修改
- ✅ 修改了 `admin-backend/app/api/group_ai/accounts.py` 文件
- ✅ 添加了 UPSERT 模式逻辑（第1074-1137行）
- ✅ 账号不存在时，如果提供了 `server_id`，会自动创建新记录，不再返回 404

### 2. 文件上传
- ✅ 已将修改后的文件上传到服务器 `ubuntu@165.154.233.55`
- ✅ 文件路径：`~/liaotian/admin-backend/app/api/group_ai/accounts.py`
- ✅ 已备份原始文件

### 3. 后端服务
- ✅ 已重启后端服务
- ⚠️ 需要验证服务是否正常运行

### 4. 测试准备
- ✅ 创建了测试脚本
- ✅ 浏览器已打开账号管理页面

## 📝 修改详情

### 核心逻辑变化

**原来的行为**：
```python
if not db_account:
    raise HTTPException(status_code=404, detail=f"賬號 {account_id} 不存在")
```

**新的行为（UPSERT）**：
```python
if not db_account:
    # UPSERT 模式：如果账号不存在，直接创建新记录
    if not request.server_id:
        raise HTTPException(status_code=400, detail="創建新賬號時必須提供 server_id")
    
    # 创建新记录
    db_account = GroupAIAccount(...)
    db.add(db_account)
    db.commit()
    # 继续更新逻辑...
```

## 🧪 测试方法

### 方法1: 直接 API 测试

```bash
# 在服务器上执行
cd ~/liaotian/admin-backend
source .venv/bin/activate

# 登录获取token
TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=changeme123' | \
  python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

# 测试 UPSERT：创建新账号
curl -X PUT "http://localhost:8000/api/v1/group-ai/accounts/639277358115" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "test-script",
    "server_id": "computer_001"
  }' \
  -v

# 预期结果：HTTP 200 或 201（不再是 404）
```

### 方法2: 使用测试脚本

```bash
# 在服务器上执行
bash ~/liaotian/deploy/完整部署并测试UPSERT.sh
```

### 方法3: 浏览器测试

1. 访问：http://aikz.usdt2026.cc/group-ai/accounts
2. 登录系统
3. 尝试"分配剧本"功能
4. 选择一个不存在的账号 ID（如 `639277358115`）
5. 填写 `script_id` 和 `server_id`
6. 提交请求
7. 应该成功创建账号，不再显示 404 错误

## ⚠️ 注意事项

1. **后端服务必须重启**：修改代码后，需要重启后端服务才能生效
   ```bash
   cd ~/liaotian/admin-backend
   source .venv/bin/activate
   pkill -f "uvicorn.*app.main:app" || true
   sleep 2
   nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
   ```

2. **必须提供 server_id**：创建新账号时，如果没有提供 `server_id`，会返回 400 错误

3. **验证文件已更新**：可以通过以下命令验证
   ```bash
   ssh ubuntu@165.154.233.55 "grep -c 'UPSERT 模式' ~/liaotian/admin-backend/app/api/group_ai/accounts.py"
   ```

## 🔍 故障排查

### 如果仍然返回 404

1. **检查文件是否已更新**：
   ```bash
   ssh ubuntu@165.154.233.55 "grep 'UPSERT 模式' ~/liaotian/admin-backend/app/api/group_ai/accounts.py"
   ```

2. **检查后端服务是否运行**：
   ```bash
   ssh ubuntu@165.154.233.55 "ps aux | grep uvicorn | grep -v grep"
   ```

3. **检查后端日志**：
   ```bash
   ssh ubuntu@165.154.233.55 "tail -50 /tmp/backend.log"
   ```

4. **重启后端服务**：
   ```bash
   ssh ubuntu@165.154.233.55 "cd ~/liaotian/admin-backend && source .venv/bin/activate && pkill -f 'uvicorn.*app.main:app' && sleep 2 && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &"
   ```

## 📊 预期结果

### 第一次调用（账号不存在）
- ✅ HTTP 状态码：200 或 201（不再是 404）
- ✅ 返回创建的账号对象
- ✅ 数据库中已创建新记录

### 第二次调用（账号已存在）
- ✅ HTTP 状态码：200
- ✅ 返回更新的账号对象
- ✅ 字段已更新

---

**部署完成时间**: 2025-11-29  
**修改文件**: `admin-backend/app/api/group_ai/accounts.py`  
**部署状态**: ✅ 文件已上传，待验证服务运行状态
