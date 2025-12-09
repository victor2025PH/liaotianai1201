# API 文檔

## 概述

本系統提供完整的 RESTful API，用於管理 Telegram AI 群組自動化系統。

## API 基礎信息

- **Base URL**: `https://aikz.usdt2026.cc/api/v1`
- **API 版本**: `v1`
- **認證方式**: JWT Bearer Token
- **文檔地址**: 
  - Swagger UI: `https://aikz.usdt2026.cc/docs`
  - OpenAPI JSON: `https://aikz.usdt2026.cc/openapi.json`
  - ReDoc: `https://aikz.usdt2026.cc/redoc` (如果配置)

## 認證

### 獲取 Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "your_password"
}
```

**響應**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 使用 Token

在後續請求中，將 Token 添加到請求頭：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 主要 API 端點

### 健康檢查

- `GET /health` - 基礎健康檢查
- `GET /healthz` - Kubernetes 健康檢查
- `GET /health?detailed=true` - 詳細健康檢查（包含所有組件狀態）

### 賬號管理

- `GET /api/v1/group-ai/accounts` - 獲取賬號列表
- `GET /api/v1/group-ai/accounts/{account_id}` - 獲取賬號詳情
- `POST /api/v1/group-ai/accounts` - 創建賬號
- `PUT /api/v1/group-ai/accounts/{account_id}` - 更新賬號
- `DELETE /api/v1/group-ai/accounts/{account_id}` - 刪除賬號

### 劇本管理

- `GET /api/v1/group-ai/scripts` - 獲取劇本列表
- `GET /api/v1/group-ai/scripts/{script_id}` - 獲取劇本詳情
- `POST /api/v1/group-ai/scripts` - 創建劇本
- `PUT /api/v1/group-ai/scripts/{script_id}` - 更新劇本
- `DELETE /api/v1/group-ai/scripts/{script_id}` - 刪除劇本

### 監控和統計

- `GET /api/v1/group-ai/dashboard` - 獲取儀表板統計
- `GET /api/v1/group-ai/monitor/accounts/metrics` - 獲取賬號指標
- `GET /api/v1/group-ai/monitor/system/statistics` - 獲取系統統計
- `GET /api/v1/group-ai/monitor/alerts` - 獲取告警列表

### 日誌管理

- `GET /api/v1/group-ai/logs` - 獲取日誌列表
- `GET /api/v1/group-ai/logs/statistics` - 獲取日誌統計
- `GET /api/v1/group-ai/logs/export` - 導出日誌（JSON/CSV）
- `GET /api/v1/group-ai/logs/error-trends` - 獲取錯誤趨勢分析

### 通知配置

- `GET /api/v1/notifications/configs` - 獲取通知配置列表
- `POST /api/v1/notifications/configs` - 創建通知配置
- `PUT /api/v1/notifications/configs/{config_id}` - 更新通知配置
- `DELETE /api/v1/notifications/configs/{config_id}` - 刪除通知配置

### 用戶管理

- `GET /api/v1/users` - 獲取用戶列表
- `GET /api/v1/users/me` - 獲取當前用戶信息
- `POST /api/v1/users` - 創建用戶
- `PUT /api/v1/users/{user_id}` - 更新用戶
- `DELETE /api/v1/users/{user_id}` - 刪除用戶

## 緩存說明

部分 API 端點已啟用緩存以提高性能：

- **賬號列表**: 30秒緩存
- **賬號詳情**: 15秒緩存
- **劇本列表**: 120秒緩存
- **劇本詳情**: 60秒緩存
- **用戶列表**: 60秒緩存
- **通知配置列表**: 300秒緩存

緩存會在相關數據更新時自動失效。

## 錯誤處理

API 使用標準 HTTP 狀態碼：

- `200 OK` - 請求成功
- `201 Created` - 資源創建成功
- `400 Bad Request` - 請求參數錯誤
- `401 Unauthorized` - 未認證或 Token 無效
- `403 Forbidden` - 無權限
- `404 Not Found` - 資源不存在
- `500 Internal Server Error` - 服務器內部錯誤
- `503 Service Unavailable` - 服務不可用

錯誤響應格式：

```json
{
  "error_code": "ERROR_CODE",
  "message": "錯誤描述",
  "technical_detail": "技術詳情（僅開發環境）"
}
```

## 限流

API 實施了請求限流以防止濫用：

- **認證端點**: 5次/分鐘
- **其他端點**: 100次/分鐘

超過限流時返回 `429 Too Many Requests`。

## 性能監控

系統提供性能監控端點：

- `GET /metrics` - Prometheus 格式的指標數據
- `GET /api/v1/system/performance/cache/stats` - 緩存統計信息

## 更多信息

詳細的 API 文檔請訪問：
- Swagger UI: `https://aikz.usdt2026.cc/docs`
- OpenAPI JSON: `https://aikz.usdt2026.cc/openapi.json`

## 更新日誌

- **2025-12-09**: 添加日誌導出和錯誤趨勢分析 API
- **2025-12-09**: 增強健康檢查端點，添加組件級別檢查
- **2025-12-09**: 優化 API 緩存策略，提升響應速度
