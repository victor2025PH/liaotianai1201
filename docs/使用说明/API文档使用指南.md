# API 文档使用指南

本文档说明如何查看和使用系统的 API 文档。

---

## 访问 API 文档

### 1. Swagger UI（交互式文档）

**URL**: `http://localhost:8000/docs`

**功能**:
- 浏览所有 API 端点
- 查看请求/响应示例
- 直接在浏览器中测试 API
- 查看数据模型定义

**使用方式**:
1. 打开浏览器访问 `http://localhost:8000/docs`
2. 点击 "Authorize" 按钮，输入 JWT Token
3. 选择要测试的 API 端点
4. 点击 "Try it out"
5. 填写参数并点击 "Execute"

### 2. ReDoc（文档式界面）

**URL**: `http://localhost:8000/redoc`

**功能**:
- 更清晰的文档展示
- 适合阅读和参考
- 包含详细的参数说明

### 3. OpenAPI JSON Schema

**URL**: `http://localhost:8000/openapi.json`

**功能**:
- 获取完整的 OpenAPI 规范
- 可用于代码生成
- 导入到 API 测试工具（如 Postman）

---

## API 端点分类

### 认证相关

- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/me` - 获取当前用户信息

### 账号管理

- `GET /api/v1/group-ai/accounts` - 获取账号列表
- `POST /api/v1/group-ai/accounts` - 创建账号
- `GET /api/v1/group-ai/accounts/{account_id}` - 获取账号详情
- `PUT /api/v1/group-ai/accounts/{account_id}` - 更新账号
- `DELETE /api/v1/group-ai/accounts/{account_id}` - 删除账号
- `POST /api/v1/group-ai/accounts/upload-session` - 上传 Session 文件
- `GET /api/v1/group-ai/accounts/scan-sessions` - 扫描 Session 文件

### Session 导出

- `GET /api/v1/group-ai/sessions/export-session/{session_name}` - 导出单个 Session
- `GET /api/v1/group-ai/sessions/export-sessions-batch` - 批量导出 Session
- `GET /api/v1/group-ai/sessions/verify-session/{session_name}` - 验证 Session

### 剧本管理

- `GET /api/v1/group-ai/scripts` - 获取剧本列表
- `POST /api/v1/group-ai/scripts` - 创建剧本
- `GET /api/v1/group-ai/scripts/{script_id}` - 获取剧本详情
- `PUT /api/v1/group-ai/scripts/{script_id}` - 更新剧本
- `DELETE /api/v1/group-ai/scripts/{script_id}` - 删除剧本

### 监控和告警

- `GET /api/v1/group-ai/monitor/health` - 健康检查
- `GET /api/v1/group-ai/monitor/alerts` - 获取告警列表
- `POST /api/v1/group-ai/monitor/alerts/check` - 执行告警检查
- `GET /api/v1/group-ai/telegram-alerts/stats` - 获取告警统计
- `POST /api/v1/group-ai/telegram-alerts/test` - 测试告警发送

### 系统监控

- `GET /health` - 快速健康检查
- `GET /health?detailed=true` - 详细健康检查
- `GET /metrics` - Prometheus 指标

---

## 认证方式

### JWT Token 认证

所有需要认证的 API 都需要在请求头中包含 JWT Token：

```bash
Authorization: Bearer <your_jwt_token>
```

### 获取 Token

```bash
# 登录获取 Token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your_password"
  }'

# 响应示例:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

### 使用 Token

```bash
# 在请求头中使用 Token
curl -X GET "http://localhost:8000/api/v1/group-ai/accounts" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 常用 API 示例

### 1. 上传 Session 文件

```bash
curl -X POST "http://localhost:8000/api/v1/group-ai/accounts/upload-session" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@account1.session"
```

### 2. 导出 Session 文件

```bash
# 导出单个 Session（含配置）
curl -X GET "http://localhost:8000/api/v1/group-ai/sessions/export-session/account1?include_config=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o account1_deploy.zip
```

### 3. 创建账号

```bash
curl -X POST "http://localhost:8000/api/v1/group-ai/accounts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "account1",
    "session_file": "account1.session",
    "script_id": 1,
    "group_ids": ["group1", "group2"],
    "active": true
  }'
```

### 4. 启动账号

```bash
curl -X POST "http://localhost:8000/api/v1/group-ai/control/accounts/account1/start" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. 获取健康状态

```bash
# 快速检查
curl http://localhost:8000/health

# 详细检查
curl "http://localhost:8000/health?detailed=true"
```

### 6. 测试 Telegram 告警

```bash
curl -X POST "http://localhost:8000/api/v1/group-ai/telegram-alerts/test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## API 响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "detail": "详细错误信息"
  }
}
```

### 分页响应

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

---

## 错误代码

### 认证错误

- `401 Unauthorized`: Token 无效或过期
- `403 Forbidden`: 权限不足

### 客户端错误

- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突

### 服务器错误

- `500 Internal Server Error`: 服务器内部错误
- `503 Service Unavailable`: 服务不可用

---

## 使用 Postman 导入

### 1. 导出 OpenAPI Schema

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

### 2. 导入到 Postman

1. 打开 Postman
2. 点击 "Import"
3. 选择 "File" 标签
4. 选择 `openapi.json` 文件
5. 点击 "Import"

### 3. 配置环境变量

在 Postman 中创建环境变量：

- `base_url`: `http://localhost:8000`
- `api_prefix`: `/api/v1`
- `token`: `<your_jwt_token>`

### 4. 使用环境变量

在请求 URL 中使用: `{{base_url}}{{api_prefix}}/group-ai/accounts`

在请求头中使用: `Authorization: Bearer {{token}}`

---

## 代码生成

### Python 客户端

```bash
# 使用 openapi-generator
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./api-client/python
```

### TypeScript 客户端

```bash
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./api-client/typescript
```

---

## 最佳实践

### 1. 错误处理

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/group-ai/accounts",
    headers={"Authorization": f"Bearer {token}"}
)

if response.status_code == 200:
    data = response.json()
    # 处理成功响应
else:
    error = response.json()
    # 处理错误
    print(f"错误: {error['error']['message']}")
```

### 2. 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_api():
    response = requests.get(...)
    response.raise_for_status()
    return response.json()
```

### 3. 请求超时

```python
response = requests.get(
    "http://localhost:8000/api/v1/group-ai/accounts",
    timeout=10  # 10 秒超时
)
```

---

## 相关文档

- [故障排查指南](故障排查指南.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
- [Session 跨服务器部署指南](SESSION跨服务器部署指南.md)

---

**文档结束**

