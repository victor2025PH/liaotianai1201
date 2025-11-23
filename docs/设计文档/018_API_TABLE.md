# API 對照表

本文檔列出 admin-backend 中所有 FastAPI 路由端點，方便前端開發、測試和運營查閱。

> **文檔版本**: v1.1  
> **最後更新**: 2025-01-17  
> **基礎路徑**: `http://localhost:8000`（開發環境）

> **重要變更**: 
> - ✅ 已恢復所有 API 端點的認證保護
> - ✅ 添加 `/healthz` 端點（Kubernetes 健康檢查）
> - ✅ 所有需要認證的端點必須在 Header 中提供 `Authorization: Bearer <access_token>`

---

## 目錄

1. [健康檢查](#健康檢查)
2. [認證模塊](#認證模塊)
3. [用戶管理模塊](#用戶管理模塊)
4. [Dashboard 模塊](#dashboard-模塊)
5. [會話管理模塊](#會話管理模塊)
6. [日誌管理模塊](#日誌管理模塊)
7. [指標監控模塊](#指標監控模塊)
8. [系統監控模塊](#系統監控模塊)
9. [告警設置模塊](#告警設置模塊)
10. [賬戶管理模塊](#賬戶管理模塊)
11. [活動記錄模塊](#活動記錄模塊)
12. [命令管理模塊](#命令管理模塊)
13. [告警管理模塊](#告警管理模塊)

---

## 健康檢查

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| health | GET | `/health` | `health_check` | 基礎健康檢查端點 | 無需認證 |
| health | GET | `/healthz` | `health_check_k8s` | Kubernetes 健康檢查端點 | 無需認證 |

**示例請求**：
```bash
# 基礎健康檢查
curl http://localhost:8000/health

# Kubernetes 健康檢查
curl http://localhost:8000/healthz
```

**預期響應**：
```json
{
  "status": "ok"
}
```

> **注意**: 健康檢查端點無需認證，可用於 Kubernetes liveness/readiness 探針。

---

## 認證模塊

**前綴**: `/api/v1/auth`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| auth | POST | `/api/v1/auth/login` | `login` | 用戶登錄，獲取 JWT Token | 無需認證 |

**請求格式**：
- Content-Type: `application/x-www-form-urlencoded`
- Body: `username=admin@example.com&password=changeme123`

**示例請求**：
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123"
```

**預期響應**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 用戶管理模塊

**前綴**: `/api/v1/users`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| users | GET | `/api/v1/users/me` | `read_current_user` | 獲取當前登錄用戶信息 | **需要認證**（Bearer Token） |
| users | GET | `/api/v1/users/` | `list_users` | 獲取所有用戶列表 | **需要超級用戶權限** |

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

---

## Dashboard 模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| dashboard | GET | `/api/v1/dashboard` | `get_dashboard` | 獲取 Dashboard 統計數據（會話總數、錯誤數、平均響應時間、Token 使用量等） | **需要認證**（Bearer Token） |

**查詢參數**：無

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
curl http://localhost:8000/api/v1/dashboard \
  -H "Authorization: Bearer <access_token>"
```

**預期響應**：
```json
{
  "stats": {
    "today_sessions": 1234,
    "success_rate": 98.2,
    "token_usage": 2400000,
    "error_count": 23,
    "avg_response_time": 1.2,
    "active_users": 892,
    "sessions_change": "+12.5%",
    "success_rate_change": "+2.1%",
    "token_usage_change": "+8.3%"
  },
  "recent_sessions": [...],
  "recent_errors": [...]
}
```

---

## 會話管理模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| sessions | GET | `/api/v1/sessions` | `list_sessions` | 獲取會話列表（支持分頁、搜索、時間範圍過濾） | **需要認證**（Bearer Token） |
| sessions | GET | `/api/v1/sessions/{session_id}` | `get_session_detail` | 獲取單個會話詳情 | **需要認證**（Bearer Token） |

**查詢參數**（`list_sessions`）：
- `page` (int, 默認: 1): 頁碼，≥ 1
- `page_size` (int, 默認: 20): 每頁數量，1-100
- `q` (string, 可選): 搜索關鍵詞（session_id 或用戶）
- `range` (string, 可選): 時間範圍（24h/7d/custom）
- `start_date` (string, 可選): 開始日期（ISO 格式）
- `end_date` (string, 可選): 結束日期（ISO 格式）

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
# 獲取會話列表（帶過濾）
curl "http://localhost:8000/api/v1/sessions?page=1&page_size=20&q=test&range=24h" \
  -H "Authorization: Bearer <access_token>"

# 獲取會話詳情
curl http://localhost:8000/api/v1/sessions/session-123 \
  -H "Authorization: Bearer <access_token>"
```

**預期響應**（`list_sessions`）：
```json
{
  "items": [
    {
      "id": "session-123",
      "user": "user@example.com",
      "status": "active",
      "started_at": "2024-12-19T10:00:00Z",
      "duration": 3600,
      "message_count": 10,
      "error_count": 0
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 日誌管理模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| logs | GET | `/api/v1/logs` | `list_logs` | 獲取日誌列表（支持分頁、級別過濾、搜索） | **需要認證**（Bearer Token） |

**查詢參數**：
- `page` (int, 默認: 1): 頁碼，≥ 1
- `page_size` (int, 默認: 20): 每頁數量，1-100
- `level` (string, 可選): 日誌級別（error/warning/info）
- `q` (string, 可選): 搜索關鍵詞

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
# 獲取錯誤日誌
curl "http://localhost:8000/api/v1/logs?page=1&page_size=20&level=error&q=timeout" \
  -H "Authorization: Bearer <access_token>"
```

**預期響應**：
```json
{
  "items": [
    {
      "id": "log-123",
      "level": "error",
      "logger": "app.api.routes",
      "message": "Request timeout",
      "timestamp": "2024-12-19T10:00:00Z",
      "source": "api",
      "metadata": {...}
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

---

## 指標監控模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| metrics | GET | `/api/v1/metrics` | `get_metrics` | 獲取指標數據（響應時間趨勢、系統狀態） | **需要認證**（Bearer Token） |

**查詢參數**：無

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
curl http://localhost:8000/api/v1/metrics \
  -H "Authorization: Bearer <access_token>"
```

**預期響應**：
```json
{
  "response_time": {
    "data_points": [
      {
        "hour": 0,
        "timestamp": "2024-12-19T00:00:00Z",
        "avg_response_time": 1.2
      }
    ],
    "average": 1.23,
    "min": 0.8,
    "max": 1.8,
    "trend": "-5%"
  },
  "system_status": {
    "status_items": [
      {
        "label": "API 服務器",
        "status": "正常",
        "value": "運行中",
        "description": "所有服務正常運行"
      }
    ],
    "last_updated": "2024-12-19T10:00:00Z"
  }
}
```

---

## 系統監控模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| monitoring | GET | `/api/v1/system/monitor` | `get_system_monitor` | 獲取系統監控數據（系統健康狀態、資源使用情況、服務狀態） | **需要認證**（Bearer Token） |

**查詢參數**：無

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
curl http://localhost:8000/api/v1/system/monitor \
  -H "Authorization: Bearer <access_token>"
```

**預期響應**：
```json
{
  "health": {
    "status": "healthy",
    "uptime": 86400,
    "version": "0.1.0"
  },
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 38.5,
    "qps": 120,
    "error_rate": 0.02
  },
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "session_service": "healthy"
  }
}
```

---

## 告警設置模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| settings | GET | `/api/v1/settings/alerts` | `get_alert_settings` | 獲取告警設置（錯誤率閾值、響應時間閾值等） | **需要認證**（Bearer Token） |
| settings | POST | `/api/v1/settings/alerts` | `save_alert_settings` | 保存告警設置 | **需要認證**（Bearer Token） |

**請求格式**（POST）：
- Content-Type: `application/json`

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
# 獲取告警設置
curl http://localhost:8000/api/v1/settings/alerts \
  -H "Authorization: Bearer <access_token>"

# 保存告警設置
curl -X POST http://localhost:8000/api/v1/settings/alerts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "error_rate_threshold": 5.0,
    "response_time_threshold": 3000,
    "notification_email": "admin@example.com"
  }'
```

**預期響應**（GET）：
```json
{
  "error_rate_threshold": 5.0,
  "response_time_threshold": 3000,
  "notification_email": "admin@example.com",
  "enabled": true
}
```

---

## 賬戶管理模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| accounts | GET | `/api/v1/accounts` | `list_accounts` | 獲取賬戶列表（Session 賬戶狀態） | **需要認證**（Bearer Token） |

**查詢參數**：無

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
curl http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer <access_token>"
```

**預期響應**：
```json
{
  "items": [
    {
      "phone": "+8613812345678",
      "displayName": "運營A",
      "roles": ["operator"],
      "status": "ONLINE",
      "lastHeartbeat": "2024-12-19T10:00:00Z"
    }
  ],
  "total": 10
}
```

---

## 活動記錄模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| activities | GET | `/api/v1/activities` | `list_activities` | 獲取活動記錄列表（紅包活動等） | **需要認證**（Bearer Token） |

**查詢參數**：無

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
curl http://localhost:8000/api/v1/activities \
  -H "Authorization: Bearer <access_token>"
```

**預期響應**：
```json
{
  "items": [
    {
      "id": "RP-20251112-001",
      "name": "双11回访红包",
      "status": "进行中",
      "success_rate": 0.86,
      "started_at": "2024-12-19T10:00:00Z",
      "participants": 18
    }
  ],
  "total": 5
}
```

---

## 命令管理模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| commands | POST | `/api/v1/commands` | `create_command` | 創建命令（發送消息、執行操作等） | **需要認證**（Bearer Token） |

**請求格式**：
- Content-Type: `application/json`

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**請求體**：
```json
{
  "account": "+8613812345678",
  "command": "send_text",
  "params": {
    "text": "Hello, World!"
  }
}
```

**示例請求**：
```bash
curl -X POST http://localhost:8000/api/v1/commands \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "account": "+8613812345678",
    "command": "send_text",
    "params": {
      "text": "Hello, World!"
    }
  }'
```

**預期響應**：
```json
{
  "commandId": "cmd-123",
  "status": "QUEUED",
  "queuedAt": "2024-12-19T10:00:00Z"
}
```

**狀態碼**：`202 Accepted`

---

## 告警管理模塊

**前綴**: `/api/v1`

| 模塊 | 方法 | 路徑 | 函數名 / 處理器 | 說明（中文） | 認證 |
|------|------|------|----------------|------------|------|
| alerts | GET | `/api/v1/alerts` | `list_alerts` | 獲取告警列表（系統告警、錯誤告警等） | **需要認證**（Bearer Token） |

**查詢參數**：無

**認證方式**：
- Header: `Authorization: Bearer <access_token>`

**示例請求**：
```bash
curl http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer <access_token>"
```

**預期響應**：
```json
{
  "items": [
    {
      "id": "AL-001",
      "level": "高",
      "title": "在線賬戶低於閾值",
      "description": "當前在線賬戶 4 個，低於設置閾值 6 個",
      "status": "未處理",
      "created_at": "2024-12-19T10:00:00Z"
    }
  ],
  "total": 3
}
```

---

## 認證狀態說明

### 當前認證狀態（2025-01-17 更新）

**✅ 已啟用認證的接口**（需要 Bearer Token）：
- `/api/v1/users/me` - 獲取當前用戶信息
- `/api/v1/users/` - 獲取所有用戶列表（需要超級用戶權限）
- `/api/v1/dashboard` - Dashboard 統計數據
- `/api/v1/sessions` - 會話列表
- `/api/v1/sessions/{session_id}` - 會話詳情
- `/api/v1/logs` - 日誌列表
- `/api/v1/metrics` - 指標數據
- `/api/v1/system/monitor` - 系統監控數據
- `/api/v1/settings/alerts` (GET/POST) - 告警設置
- `/api/v1/accounts` - 賬戶列表
- `/api/v1/activities` - 活動記錄列表
- `/api/v1/commands` - 創建命令
- `/api/v1/alerts` - 告警列表
- `/api/v1/group-ai/*` - 所有群組 AI 相關路由

**無需認證的接口**：
- `/health` - 基礎健康檢查
- `/healthz` - Kubernetes 健康檢查（與 `/health` 相同）
- `/api/v1/auth/login` - 用戶登入（獲取 Token）

### 認證方式

所有需要認證的接口都必須在請求 Header 中提供有效的 Bearer Token：

```bash
Authorization: Bearer <access_token>
```

**獲取 Token**：

1. 調用登入接口：
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@example.com&password=changeme123"
   ```

2. 從響應中獲取 `access_token`

3. 在後續請求中使用 Token：
   ```bash
   curl http://localhost:8000/api/v1/dashboard \
     -H "Authorization: Bearer <access_token>"
   ```

### 生產環境要求

**✅ 已完成**：所有 API 端點已啟用認證保護。在生產環境部署前，確保：

1. ✅ 所有 API 請求都包含有效的 Bearer Token：
   ```
   Authorization: Bearer <access_token>
   ```

3. 配置適當的 CORS 策略，限制允許的來源。

---

## API 使用示例

### 完整流程：登錄 → 獲取數據

```bash
# 1. 登錄獲取 Token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" \
  | jq -r '.access_token')

# 2. 使用 Token 訪問受保護的接口（生產環境）
curl http://localhost:8000/api/v1/dashboard \
  -H "Authorization: Bearer $TOKEN"

# 3. 獲取會話列表
curl "http://localhost:8000/api/v1/sessions?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 錯誤響應格式

所有 API 在發生錯誤時，會返回標準的錯誤響應：

```json
{
  "detail": "錯誤描述信息"
}
```

**常見 HTTP 狀態碼**：
- `200 OK` - 請求成功
- `202 Accepted` - 請求已接受（異步處理）
- `400 Bad Request` - 請求參數錯誤
- `401 Unauthorized` - 未認證或 Token 無效
- `403 Forbidden` - 無權限訪問
- `404 Not Found` - 資源不存在
- `422 Unprocessable Entity` - 數據驗證失敗
- `500 Internal Server Error` - 服務器內部錯誤

---

## 快速參考

### 按功能分組

**數據查詢**：
- Dashboard: `GET /api/v1/dashboard`
- Sessions: `GET /api/v1/sessions`, `GET /api/v1/sessions/{id}`
- Logs: `GET /api/v1/logs`
- Metrics: `GET /api/v1/metrics`
- System Monitor: `GET /api/v1/system/monitor`

**配置管理**：
- Alert Settings: `GET /api/v1/settings/alerts`, `POST /api/v1/settings/alerts`

**資源管理**：
- Accounts: `GET /api/v1/accounts`
- Activities: `GET /api/v1/activities`
- Alerts: `GET /api/v1/alerts`
- Commands: `POST /api/v1/commands`

**認證與用戶**：
- Login: `POST /api/v1/auth/login`
- Current User: `GET /api/v1/users/me`
- List Users: `GET /api/v1/users/`

---

**最後更新**: 2024-12-19  
**文檔維護**: 請根據實際代碼變更及時更新本文檔

