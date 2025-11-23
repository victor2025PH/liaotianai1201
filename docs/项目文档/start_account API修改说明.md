# start_account API修改说明

## 修改内容

### 1. 添加了 `start_account_on_server` 函数

**位置**: `admin-backend/app/api/group_ai/accounts.py`

**功能**:
- 通过SSH连接到远程服务器
- 在服务器上执行启动命令来启动账号
- 返回启动结果

**实现细节**:
- 使用 `paramiko` 库进行SSH连接
- 检查账号是否已在服务器上运行
- 如果未运行，执行Python命令启动账号
- 将启动日志保存到 `logs/account_{account_id}.log`

### 2. 修改了 `start_account` API

**位置**: `admin-backend/app/api/group_ai/accounts.py`

**修改逻辑**:
1. 首先检查数据库中的账号记录
2. 如果账号有 `server_id`：
   - 调用 `start_account_on_server` 在服务器上启动
   - 返回服务器启动结果
3. 如果账号没有 `server_id`：
   - 使用原有逻辑在本地启动（保持向后兼容）

## 代码变更

### 新增函数

```python
async def start_account_on_server(
    account_id: str,
    server_id: str,
    db: Session
) -> bool:
    """在遠程服務器上啟動賬號"""
    # 1. 加载服务器配置
    # 2. 通过SSH连接服务器
    # 3. 检查账号是否已运行
    # 4. 执行启动命令
    # 5. 返回结果
```

### 修改的API

```python
@router.post("/{account_id}/start")
async def start_account(...):
    # 检查账号的 server_id
    if db_account.server_id:
        # 在服务器上启动
        return await start_account_on_server(...)
    else:
        # 在本地启动（旧逻辑）
        return await start_account_local(...)
```

## 使用方式

### 1. 创建账号（自动分配到服务器）

```powershell
POST /api/v1/group-ai/accounts
{
  "account_id": "test_account",
  "session_file": "sessions/test.session",
  "script_id": "000新人欢迎剧本"
}
# 系统会自动分配服务器并上传session文件
```

### 2. 启动账号（自动在服务器上启动）

```powershell
POST /api/v1/group-ai/accounts/{account_id}/start
# 如果account有server_id，会在服务器上启动
# 如果account没有server_id，会在本地启动
```

## 注意事项

### 服务器要求

1. **项目代码**: 服务器上需要有完整的项目代码
2. **Python依赖**: 服务器上需要安装所有Python依赖
3. **环境变量**: 服务器上需要配置正确的环境变量（API_ID, API_HASH等）
4. **SSH访问**: 需要能够通过SSH连接到服务器

### 启动命令

当前实现使用直接运行Python命令的方式启动账号。如果服务器上有其他启动方式（如systemd服务、启动脚本等），可能需要调整启动命令。

### 日志

账号启动日志保存在服务器的 `logs/account_{account_id}.log` 文件中，可以通过SSH查看。

## 测试

使用 `测试服务器部署和启动.ps1` 脚本进行测试：

```powershell
pwsh -File "测试服务器部署和启动.ps1"
```

测试流程：
1. 登录获取Token
2. 检查服务器列表
3. 扫描本地session文件
4. 获取剧本列表
5. 创建测试账号（自动分配到服务器）
6. 启动账号（应该在服务器上启动）
7. 检查账号状态

## 后续优化

1. **启动方式优化**: 根据实际部署方式调整启动命令
2. **错误处理**: 增强错误处理和日志记录
3. **状态同步**: 实现服务器上账号状态的实时同步
4. **健康检查**: 添加服务器上账号的健康检查机制

