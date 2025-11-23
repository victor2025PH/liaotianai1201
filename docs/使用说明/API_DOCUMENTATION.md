# API 文档

> **更新日期**: 2025-01-17  
> **API 版本**: v1.0

---

## 📋 目录

1. [API 概览](#api-概览)
2. [认证](#认证)
3. [API 端点](#api-端点)
4. [请求/响应格式](#请求响应格式)
5. [错误处理](#错误处理)
6. [示例代码](#示例代码)

---

## API 概览

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **API 版本**: v1
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`

### 交互式文档

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### 健康检查

- **`GET /health`** - 基础健康检查（无需认证）
- **`GET /healthz`** - Kubernetes 健康检查（无需认证）

```bash
# 健康检查
curl http://localhost:8000/health
# 响应: {"status":"ok"}
```

---

## 认证

### 获取访问令牌

**端点**: `POST /api/v1/auth/login`

**请求格式**: `application/x-www-form-urlencoded`

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123"
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 使用令牌

在请求头中添加 `Authorization` 字段：

```bash
curl -X GET "http://localhost:8000/api/v1/dashboard" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Python 示例**:
```python
import requests

# 登录获取令牌
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={
        "username": "admin@example.com",
        "password": "changeme123"
    }
)
token = response.json()["access_token"]

# 使用令牌访问 API
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/dashboard",
    headers=headers
)
```

---

## API 端点

### 认证端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/v1/auth/login` | 用户登录 | ❌ |

### Dashboard 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/dashboard` | 获取 Dashboard 数据 | ✅ |

### 账户管理端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/accounts` | 获取账户列表 | ✅ |
| `POST` | `/api/v1/accounts` | 创建账户 | ✅ |
| `GET` | `/api/v1/accounts/{id}` | 获取账户详情 | ✅ |
| `PUT` | `/api/v1/accounts/{id}` | 更新账户 | ✅ |
| `DELETE` | `/api/v1/accounts/{id}` | 删除账户 | ✅ |

### 会话管理端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/sessions` | 获取会话列表 | ✅ |
| `GET` | `/api/v1/sessions/{id}` | 获取会话详情 | ✅ |

### 日志管理端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/logs` | 获取日志列表 | ✅ |

### 指标端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/metrics` | 获取系统指标 | ✅ |

### 系统监控端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/system/monitor` | 获取系统监控数据 | ✅ |

### 群组 AI 端点

#### 账号管理

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/group-ai/accounts` | 获取群组 AI 账号列表 | ✅ |
| `POST` | `/api/v1/group-ai/accounts` | 创建群组 AI 账号 | ✅ |
| `GET` | `/api/v1/group-ai/accounts/{id}` | 获取账号详情 | ✅ |
| `PUT` | `/api/v1/group-ai/accounts/{id}` | 更新账号 | ✅ |
| `DELETE` | `/api/v1/group-ai/accounts/{id}` | 删除账号 | ✅ |
| `POST` | `/api/v1/group-ai/accounts/{id}/start` | 启动账号 | ✅ |
| `POST` | `/api/v1/group-ai/accounts/{id}/stop` | 停止账号 | ✅ |
| `GET` | `/api/v1/group-ai/accounts/{id}/status` | 获取账号状态 | ✅ |

#### 剧本管理

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/group-ai/scripts` | 获取剧本列表 | ✅ |
| `POST` | `/api/v1/group-ai/scripts` | 创建剧本 | ✅ |
| `GET` | `/api/v1/group-ai/scripts/{id}` | 获取剧本详情 | ✅ |
| `PUT` | `/api/v1/group-ai/scripts/{id}` | 更新剧本 | ✅ |
| `DELETE` | `/api/v1/group-ai/scripts/{id}` | 删除剧本 | ✅ |
| `POST` | `/api/v1/group-ai/scripts/upload` | 上传剧本文件 | ✅ |

#### 群组管理

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `POST` | `/api/v1/group-ai/groups/create` | 创建群组 | ✅ |
| `POST` | `/api/v1/group-ai/groups/join` | 加入群组 | ✅ |
| `POST` | `/api/v1/group-ai/groups/start-chat` | 启动群组聊天 | ✅ |

#### 监控端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| `GET` | `/api/v1/group-ai/monitor/accounts/{id}/metrics` | 获取账号指标 | ✅ |
| `GET` | `/api/v1/group-ai/monitor/system/metrics` | 获取系统指标 | ✅ |
| `GET` | `/api/v1/group-ai/monitor/alerts` | 获取告警列表 | ✅ |

---

## 请求/响应格式

### 标准请求格式

```json
{
  "field1": "value1",
  "field2": "value2"
}
```

### 标准响应格式

**成功响应**:
```json
{
  "id": "123",
  "name": "Example",
  "status": "active"
}
```

**列表响应**:
```json
{
  "items": [
    {"id": "1", "name": "Item 1"},
    {"id": "2", "name": "Item 2"}
  ],
  "total": 2,
  "page": 1,
  "page_size": 10
}
```

### 分页参数

- `page` (int, 默认: 1) - 页码（从 1 开始）
- `page_size` (int, 默认: 10, 最大: 100) - 每页数量

**示例**:
```bash
GET /api/v1/sessions?page=1&page_size=20
```

---

## 错误处理

### 标准错误响应

```json
{
  "detail": "错误描述信息"
}
```

### HTTP 状态码

| 状态码 | 说明 | 示例 |
|--------|------|------|
| `200` | 成功 | 请求成功 |
| `201` | 创建成功 | 资源创建成功 |
| `204` | 无内容 | 删除成功 |
| `400` | 错误请求 | 请求参数错误 |
| `401` | 未授权 | Token 无效或过期 |
| `403` | 禁止访问 | 无权限访问 |
| `404` | 未找到 | 资源不存在 |
| `422` | 验证错误 | 请求体验证失败 |
| `500` | 服务器错误 | 内部服务器错误 |

### 错误示例

**401 未授权**:
```json
{
  "detail": "Not authenticated"
}
```

**404 未找到**:
```json
{
  "detail": "Account not found"
}
```

**422 验证错误**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 示例代码

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. 登录
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "admin@example.com",
        "password": "changeme123"
    }
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. 获取 Dashboard
response = requests.get(
    f"{BASE_URL}/dashboard",
    headers=headers
)
dashboard = response.json()

# 3. 获取账户列表
response = requests.get(
    f"{BASE_URL}/group-ai/accounts",
    headers=headers,
    params={"page": 1, "page_size": 10}
)
accounts = response.json()

# 4. 创建账户
response = requests.post(
    f"{BASE_URL}/group-ai/accounts",
    headers=headers,
    json={
        "account_id": "test_account",
        "session_file": "test.session",
        "script_id": "default",
        "group_ids": [123456],
        "active": True
    }
)
new_account = response.json()
```

### JavaScript/TypeScript

```typescript
const BASE_URL = "http://localhost:8000/api/v1";

// 1. 登录
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: "POST",
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
  },
  body: new URLSearchParams({
    username: "admin@example.com",
    password: "changeme123",
  }),
});
const { access_token } = await loginResponse.json();

// 2. 获取 Dashboard
const dashboardResponse = await fetch(`${BASE_URL}/dashboard`, {
  headers: {
    Authorization: `Bearer ${access_token}`,
  },
});
const dashboard = await dashboardResponse.json();

// 3. 获取账户列表
const accountsResponse = await fetch(
  `${BASE_URL}/group-ai/accounts?page=1&page_size=10`,
  {
    headers: {
      Authorization: `Bearer ${access_token}`,
    },
  }
);
const accounts = await accountsResponse.json();
```

### cURL

```bash
# 1. 登录
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" \
  | jq -r '.access_token')

# 2. 获取 Dashboard
curl -X GET "http://localhost:8000/api/v1/dashboard" \
  -H "Authorization: Bearer $TOKEN"

# 3. 获取账户列表
curl -X GET "http://localhost:8000/api/v1/group-ai/accounts?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 详细 API 文档

### 交互式文档

访问 Swagger UI 查看完整的交互式 API 文档：

```
http://localhost:8000/docs
```

### API 对照表

查看 `docs/设计文档/018_API_TABLE.md` 获取详细的 API 端点列表和说明。

---

## 相关文档

- `docs/使用说明/DOCKER_DEPLOYMENT.md` - Docker 部署指南
- `docs/使用说明/DEPLOYMENT_GUIDE.md` - 完整部署指南
- `admin-backend/docs/MIGRATION_GUIDE.md` - 数据库迁移指南
- `docs/设计文档/018_API_TABLE.md` - API 对照表

---

**文档维护**: 如有问题或建议，请提交 Issue 或 Pull Request。

