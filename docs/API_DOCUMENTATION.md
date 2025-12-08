# API 文档

本文档提供完整的 API 接口说明。

## 基础信息

- **Base URL**: `https://your-domain.com/api/v1`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`

## 认证

### 登录获取Token

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@example.com&password=your_password
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 使用Token

在请求头中添加：
```
Authorization: Bearer {access_token}
```

## 核心API

### 健康检查

#### 基础健康检查
```http
GET /health
```

#### 详细健康检查
```http
GET /health?detailed=true
```

#### K8s健康检查
```http
GET /healthz
```

### 性能监控

#### 获取性能统计
```http
GET /api/v1/system/performance
Authorization: Bearer {token}
```

**响应**:
```json
{
  "request_count": 1234,
  "average_response_time_ms": 45.2,
  "total_response_time_ms": 55800,
  "slow_requests_count": 5,
  "slow_requests": [...],
  "requests_by_endpoint": {...},
  "requests_by_status": {...}
}
```

## 群组AI API

### 账号管理

#### 获取账号列表
```http
GET /api/v1/group-ai/accounts
Authorization: Bearer {token}
```

**查询参数**:
- `skip`: 跳过数量 (默认: 0)
- `limit`: 每页数量 (默认: 100)
- `search`: 搜索关键词
- `status`: 状态过滤 (active/inactive)

#### 创建账号
```http
POST /api/v1/group-ai/accounts
Authorization: Bearer {token}
Content-Type: application/json

{
  "phone_number": "+1234567890",
  "script_id": "script-uuid",
  "server_id": "server-uuid"
}
```

#### 更新账号
```http
PUT /api/v1/group-ai/accounts/{account_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "active": true,
  "script_id": "new-script-uuid"
}
```

#### 删除账号
```http
DELETE /api/v1/group-ai/accounts/{account_id}
Authorization: Bearer {token}
```

### 脚本管理

#### 获取脚本列表
```http
GET /api/v1/group-ai/scripts
Authorization: Bearer {token}
```

**查询参数**:
- `skip`: 跳过数量
- `limit`: 每页数量
- `search`: 搜索关键词
- `status`: 状态过滤 (draft/reviewing/published/disabled)
- `sort_by`: 排序字段 (name/created_at/updated_at/status)
- `sort_order`: 排序顺序 (asc/desc)

#### 创建脚本
```http
POST /api/v1/group-ai/scripts
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "脚本名称",
  "description": "脚本描述",
  "content": {
    "script_id": "script-001",
    "version": "1.0.0",
    "scenes": [...]
  }
}
```

#### 更新脚本
```http
PUT /api/v1/group-ai/scripts/{script_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "更新后的名称",
  "content": {...}
}
```

### 监控API

#### 获取账号指标
```http
GET /api/v1/group-ai/monitor/accounts/metrics
Authorization: Bearer {token}
```

**查询参数**:
- `account_id`: 账号ID (可选)

#### 获取系统统计
```http
GET /api/v1/group-ai/monitor/system/statistics
Authorization: Bearer {token}
```

**查询参数**:
- `period`: 时间范围 (1h/24h/7d/30d, 默认: 24h)

#### 获取告警列表
```http
GET /api/v1/group-ai/monitor/alerts
Authorization: Bearer {token}
```

**查询参数**:
- `limit`: 返回数量 (默认: 50)
- `alert_type`: 告警类型 (error/warning/info)
- `resolved`: 是否已解决 (true/false)
- `use_aggregation`: 是否使用聚合 (默认: true)

### 告警管理API

#### 获取告警统计
```http
GET /api/v1/group-ai/alert-management/statistics
Authorization: Bearer {token}
```

**响应**:
```json
{
  "total_alerts": 100,
  "deduplicated": 20,
  "aggregated": 15,
  "suppressed": 5,
  "resolved": 60,
  "active_by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 8,
    "low": 5
  },
  "total_active": 20,
  "total_aggregated": 15
}
```

#### 静默告警
```http
POST /api/v1/group-ai/alert-management/{alert_key}/suppress
Authorization: Bearer {token}
Content-Type: application/json

{
  "duration_seconds": 3600,
  "reason": "正在处理中"
}
```

#### 确认告警
```http
POST /api/v1/group-ai/alert-management/{alert_key}/acknowledge
Authorization: Bearer {token}
Content-Type: application/json

{
  "acknowledged_by": "admin@example.com"
}
```

### 日志API

#### 获取日志列表
```http
GET /api/v1/group-ai/logs
Authorization: Bearer {token}
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)
- `level`: 日志级别 (error/warning/info)
- `q`: 搜索关键词
- `source`: 来源过滤
- `start_time`: 开始时间 (ISO 8601)
- `end_time`: 结束时间 (ISO 8601)

#### 获取日志统计
```http
GET /api/v1/group-ai/logs/statistics
Authorization: Bearer {token}
```

### 仪表板API

#### 获取仪表板数据
```http
GET /api/v1/group-ai/dashboard
Authorization: Bearer {token}
```

**响应**:
```json
{
  "stats": {
    "total_accounts": 100,
    "active_accounts": 80,
    "total_scripts": 20,
    "total_messages": 50000
  },
  "recent_sessions": [...],
  "recent_errors": [...]
}
```

## 用户管理API

### 获取当前用户
```http
GET /api/v1/users/me
Authorization: Bearer {token}
```

### 获取用户列表
```http
GET /api/v1/users
Authorization: Bearer {token}
```

### 创建用户
```http
POST /api/v1/users
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "用户姓名"
}
```

## 通知API

### 获取通知列表
```http
GET /api/v1/notifications
Authorization: Bearer {token}
```

**查询参数**:
- `skip`: 跳过数量
- `limit`: 每页数量
- `read`: 是否已读 (true/false)
- `notification_type`: 通知类型

### 标记通知为已读
```http
PUT /api/v1/notifications/{notification_id}/read
Authorization: Bearer {token}
```

## 错误响应

所有API在出错时返回以下格式：

```json
{
  "detail": "错误描述",
  "error_code": "ERROR_CODE",
  "status_code": 400
}
```

### 常见错误码

- `401 Unauthorized`: 未认证或token无效
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `422 Validation Error`: 请求参数验证失败
- `500 Internal Server Error`: 服务器内部错误

## 速率限制

- 认证API: 5次/分钟
- 其他API: 100次/分钟

超过限制将返回 `429 Too Many Requests`。

## OpenAPI文档

访问 `/docs` 查看完整的交互式API文档（Swagger UI）。

访问 `/openapi.json` 获取OpenAPI规范JSON。

