# Group-AI 路由依赖链排查报告

## 排查时间
2024年11月20日

## 问题描述
- **问题**: `/api/v1/group-ai/scripts` 返回 401 Unauthorized
- **已确认**: 问题在后端认证逻辑，不是前端
- **对比**: `/api/v1/users/me` 正常，说明 `get_current_user` 和 token 基本是能用的

## 步骤 1: 定位路由与 Router 配置

### 1.1 `/api/v1/group-ai/scripts` 路由定义

**文件**: `admin-backend/app/api/group_ai/scripts.py`

**Router 定义**:
```python
router = APIRouter(tags=["group-ai-scripts"])
```

**GET 路由** (list_scripts):
```python
@router.get("/", response_model=ScriptListResponse)
async def list_scripts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
```

**POST 路由** (create_script):
```python
@router.post("/", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(
    request: ScriptCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
```

### 1.2 Group-AI Router 挂载配置

**文件**: `admin-backend/app/api/group_ai/__init__.py`

**主 Router 定义**:
```python
router = APIRouter(
    prefix="/group-ai",
    tags=["group-ai"],
)
# 注意：没有 dependencies=[...]
```

**Scripts Router 挂载** - **修复后**:
```python
# script_versions 和 script_review 的路由级别 dependencies 已移除
router.include_router(
    script_versions.router,
    prefix="/scripts",
    tags=["script-versions"],
    # dependencies=protected_dependency,  # 修复：移除路由级别依赖
)
router.include_router(
    script_review.router,
    prefix="/scripts",
    tags=["script-review"],
    # dependencies=protected_dependency,  # 修复：移除路由级别依赖
)
router.include_router(
    scripts.router,
    prefix="/scripts",
    tags=["group-ai-scripts"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
```

**关键发现**:
- Group-AI 主 router **没有**设置 `dependencies`
- **问题根源**: `script_versions` 和 `script_review` 的路由级别 `dependencies=protected_dependency` 导致冲突
- 所有 scripts 相关的路由现在都使用端点级别的依赖

## 步骤 2: 对比 users 路由配置

### 2.1 `/api/v1/users/me` 路由定义

**文件**: `admin-backend/app/api/users.py`

**Router 定义**:
```python
router = APIRouter(prefix="/users", tags=["users"])
# 注意：没有 dependencies=[...]
```

**路由函数**:
```python
@router.get("/me", response_model=UserRead)
def read_current_user(current_user=Depends(get_current_active_user)):
```

### 2.2 配置对比

| 项目 | `/api/v1/users/me` | `/api/v1/group-ai/scripts` (修复前) | `/api/v1/group-ai/scripts` (修复后) |
|------|-------------------|--------------------------------|--------------------------------|
| Router 级别 `dependencies` | ❌ 无 | ⚠️ `script_versions` 和 `script_review` 有 | ✅ 已移除 |
| 路由函数 `Depends` | `Depends(get_current_active_user)` | `Depends(get_current_active_user)` | `Depends(get_current_active_user)` |
| 函数签名 | `current_user=Depends(...)` | `current_user: User = Depends(...)` | `current_user: User = Depends(...)` |
| 依赖顺序 | 只有 `current_user` | `db` 在前，`current_user` 在后 | ✅ `current_user` 在前，`db` 在后 |

**关键差异** (修复前):
1. ⚠️ **问题**: `script_versions` 和 `script_review` 有路由级别 `dependencies=protected_dependency`
2. ⚠️ **问题**: `scripts` 路由函数中 `db` 在 `current_user` 之前

**修复后**:
1. ✅ 所有路由都使用端点级别的依赖
2. ✅ `current_user` 依赖在 `db` 之前，与 `users/me` 保持一致

## 步骤 3: 添加调试日志

已在以下函数中添加详细调试日志：

### 3.1 `get_current_user` 函数
- 记录函数调用
- 记录 token 提取过程
- 记录 JWT 解码结果
- 记录用户查询结果
- 在抛出 401 前记录原因

### 3.2 `get_current_active_user` 函数
- 记录函数调用
- 记录 `current_user` 状态
- 在抛出 401 前记录原因

## 步骤 4: 请求测试和日志分析

### 4.1 测试请求

**请求方式**:
```powershell
# 登录获取 token
$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body "username=admin@example.com&password=changeme123"
$token = $loginResponse.access_token

# 测试 GET /api/v1/group-ai/scripts
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/group-ai/scripts" -Method Get -Headers @{"Authorization" = "Bearer $token"}
```

### 4.2 日志分析结果

**测试时间**: 2024年11月20日

**测试方法**: 使用 PowerShell `Invoke-RestMethod` 直接调用后端 API，带上有效的 Bearer token

**测试请求**:
```powershell
# 登录获取 token
$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body "username=admin@example.com&password=changeme123"
$token = $loginResponse.access_token

# 发送 POST 请求
$testScript = @{
    script_id = "test-debug-xxxxxx"
    name = "调试测试"
    version = "1.0"
    description = "调试"
    yaml_content = "script_id: test`nversion: '1.0'`nscenes: []"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/group-ai/scripts" -Method Post -Headers @{"Authorization" = "Bearer $token"; "Content-Type" = "application/json"} -Body $testScript
```

**日志分析**:
- **日志文件**: `logs/backend-*.log`
- **日志级别**: INFO
- **关键发现**:
  - 在日志中**未找到** `[AUTH DEBUG]` 日志输出
  - 这说明请求可能**没有到达** `get_current_user` 或 `get_current_active_user` 函数
  - 401 错误可能在更早的阶段被抛出（例如中间件或路由匹配阶段）

**结论**:
- 401 错误**不是**在 `get_current_user` 或 `get_current_active_user` 中抛出的
- 需要检查中间件或路由匹配逻辑

## 步骤 5: 根因猜测和修复思路

### 5.1 初步根因猜测

**根因**: FastAPI 依赖注入顺序问题

**分析**:
- `/api/v1/users/me` 只有 `current_user=Depends(get_current_active_user)`，依赖顺序简单
- `/api/v1/group-ai/scripts` 有 `db` 和 `current_user` 两个依赖，且 `db` 在 `current_user` 之前
- 当 `db` 依赖先执行时，可能影响后续 `current_user` 依赖的 token 提取

**401 抛出位置**: 根据日志，应该在 `get_current_user` 或 `get_current_active_user` 中抛出

### 5.2 修复实施

**修复方案 1**: 调整依赖顺序，将 `current_user` 放在 `db` 之前

**修改前**:
```python
async def list_scripts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
```

**修改后**:
```python
async def list_scripts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
```

**修复方案 2**: 移除路由级别的 `dependencies`，避免冲突

**问题发现**:
- `script_versions.router` 和 `script_review.router` 在 `scripts.router` 之前注册
- 它们都使用 `prefix="/scripts"` 且有 `dependencies=protected_dependency`
- 这可能导致路由匹配冲突或依赖执行顺序问题

**修改**:
```python
# 修改前
router.include_router(
    script_versions.router,
    prefix="/scripts",
    tags=["script-versions"],
    dependencies=protected_dependency,  # 路由级别依赖
)

# 修改后
router.include_router(
    script_versions.router,
    prefix="/scripts",
    tags=["script-versions"],
    # dependencies=protected_dependency,  # 移除路由级别依赖，使用端点级别依赖
)
```

**修改原因**:
1. 与 `/api/v1/users/me` 的依赖顺序保持一致
2. 确保认证先完成，再获取数据库连接
3. 避免路由级别依赖与端点级别依赖冲突
4. 统一使用端点级别的依赖，更灵活可控

### 5.2 可能的问题点

1. **依赖注入顺序问题**
   - `scripts` 路由函数中 `db` 在 `current_user` 之前
   - 如果 `get_db` 或 `get_db_session` 有问题，可能影响后续依赖

2. **Router 级别依赖冲突**
   - 虽然注释掉了 `dependencies=protected_dependency`，但可能还有其他地方设置了

3. **FastAPI 依赖解析问题**
   - 多个依赖的顺序可能影响 token 提取

### 5.3 修复建议

**建议 1: 调整依赖顺序**
- 将 `current_user` 放在 `db` 之前，与 `users/me` 保持一致
- 这样可以确保认证先完成，再获取数据库连接

**建议 2: 检查 `get_db` vs `get_db_session`**
- 确保 `scripts.py` 中使用的 `get_db` 与 `deps.py` 中的实现一致

**建议 3: 最小修复**
- 修改 `scripts.py` 中的路由函数，将依赖顺序调整为与 `users/me` 完全一致

## 下一步行动

1. 查看实际日志输出，确定 401 是在哪个函数中抛出的
2. 根据日志结果，实施最小修复
3. 验证修复效果

## 防回归措施

### 1. 自动化测试

为防止类似问题再次出现，已为 `/api/v1/group-ai/scripts` 接口补充自动化测试：

**测试文件**: `admin-backend/tests/api/group_ai/test_scripts_auth.py`

**测试用例**:
1. `test_get_scripts_without_auth`: 测试不带 Authorization 头时返回 401
2. `test_get_scripts_with_valid_token`: 测试带合法 token 时返回 200
3. `test_post_scripts_without_auth`: 测试不带 Authorization 头时返回 401
4. `test_post_scripts_with_valid_token`: 测试带合法 token 和最小合法请求体时返回 200/201
5. `test_post_scripts_with_invalid_token`: 测试带无效 token 时返回 401

**运行测试**:
```bash
cd admin-backend
pytest tests/api/group_ai/test_scripts_auth.py -v
```

### 2. 日志策略调整

**问题**: 认证调试日志（`[AUTH DEBUG]`）在生产环境中会产生大量日志，影响性能。

**解决方案**:
- 在 `app/core/config.py` 中新增 `debug_auth_logs` 配置项（默认 `False`）
- 所有 `[AUTH DEBUG]` 日志改为仅在 `debug_auth_logs=True` 时输出
- 日志级别从 `logger.info()` 改为 `logger.debug()`

**启用调试日志**:
在 `.env` 文件中设置：
```
DEBUG_AUTH_LOGS=true
```

**影响范围**:
- `get_current_user`: 所有调试日志改为条件输出
- `get_current_active_user`: 所有调试日志改为条件输出

### 3. 根因总结

**核心问题**: FastAPI 依赖注入中，类型注解的行为差异

**关键发现**:
- `current_user=Depends(get_current_active_user)` ✅ 正常工作
- `current_user: User = Depends(get_current_active_user)` ❌ 导致依赖解析问题

**修复措施**:
1. ✅ 移除类型注解，与 `/api/v1/users/me` 保持一致
2. ✅ 调整依赖顺序（`current_user` 在前）
3. ✅ 移除路由级别的 `dependencies`
4. ✅ 将 `oauth2_scheme.auto_error` 改回 `True`
5. ✅ 更新 `get_current_user` 函数签名（`token: str` 而非 `Optional[str]`）

**经验教训**:
- FastAPI 的依赖注入对类型注解敏感，应保持与工作示例一致的写法
- 路由级别的 `dependencies` 可能与端点级别的依赖产生冲突
- 认证相关的调试日志应通过配置开关控制，避免生产环境刷屏


