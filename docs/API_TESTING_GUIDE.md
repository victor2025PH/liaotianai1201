# API 測試指南

> **目的**: 使用 Swagger UI 和 curl 測試所有 API 端點

---

## 🚀 快速開始

### 方法 1: 使用 Swagger UI（推薦）

1. **訪問 Swagger UI**
   - URL: `https://aikz.usdt2026.cc/docs`
   - 或: `http://localhost:8000/docs`（本地開發）

2. **獲取 Token**
   - 使用 `/api/v1/auth/login` 端點登錄
   - 複製返回的 `access_token`

3. **設置認證**
   - 點擊右上角的 "Authorize" 按鈕
   - 輸入: `Bearer YOUR_ACCESS_TOKEN`
   - 點擊 "Authorize"

4. **測試 API**
   - 選擇要測試的端點
   - 點擊 "Try it out"
   - 填寫參數
   - 點擊 "Execute"

---

### 方法 2: 使用 curl（命令行）

```bash
# 1. 登錄獲取 Token
TOKEN=$(curl -X POST "https://aikz.usdt2026.cc/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"your_password"}' \
  | jq -r '.access_token')

# 2. 使用 Token 測試 API
curl -X GET "https://aikz.usdt2026.cc/api/v1/group-ai/accounts" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📋 API 測試清單

### ✅ 1. 認證 API

#### 1.1 登錄
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "your_password"
}
```

**預期響應**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**測試點**:
- [ ] 正確的憑據 → 返回 Token
- [ ] 錯誤的憑據 → 返回 401
- [ ] 缺少字段 → 返回 422

#### 1.2 測試 Token
```bash
POST /api/v1/auth/test-token
Authorization: Bearer YOUR_TOKEN
```

**預期響應**:
```json
{
  "id": 1,
  "email": "admin@example.com",
  "is_active": true,
  "is_superuser": true
}
```

**測試點**:
- [ ] 有效的 Token → 返回用戶信息
- [ ] 無效的 Token → 返回 401
- [ ] 過期的 Token → 返回 401

---

### ✅ 2. 賬號管理 API

#### 2.1 獲取賬號列表
```bash
GET /api/v1/group-ai/accounts?page=1&page_size=20
Authorization: Bearer YOUR_TOKEN
```

**預期響應**:
```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

**測試點**:
- [ ] 基本列表查詢
- [ ] 分頁功能（page, page_size）
- [ ] 搜索功能（search 參數）
- [ ] 篩選功能（status_filter, script_id）
- [ ] 排序功能（sort_by, sort_order）
- [ ] 緩存測試（重複請求，檢查響應時間）

#### 2.2 獲取賬號詳情
```bash
GET /api/v1/group-ai/accounts/{account_id}
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 存在的賬號 ID → 返回詳情
- [ ] 不存在的賬號 ID → 返回 404
- [ ] 緩存測試

#### 2.3 創建賬號
```bash
POST /api/v1/group-ai/accounts
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "account_name": "test_account",
  "script_id": "script_123",
  "server_id": "server_1"
}
```

**測試點**:
- [ ] 有效的數據 → 創建成功
- [ ] 無效的數據 → 返回 422
- [ ] 缺少必填字段 → 返回 422
- [ ] 創建後檢查緩存是否失效

#### 2.4 更新賬號
```bash
PUT /api/v1/group-ai/accounts/{account_id}
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "account_name": "updated_name"
}
```

**測試點**:
- [ ] 更新成功
- [ ] 更新後檢查緩存是否失效

#### 2.5 刪除賬號
```bash
DELETE /api/v1/group-ai/accounts/{account_id}
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 刪除成功
- [ ] 刪除後檢查緩存是否失效

#### 2.6 賬號操作
```bash
POST /api/v1/group-ai/accounts/{account_id}/start
POST /api/v1/group-ai/accounts/{account_id}/stop
POST /api/v1/group-ai/accounts/{account_id}/restart
```

**測試點**:
- [ ] 啟動/停止/重啟操作成功
- [ ] 狀態正確更新

---

### ✅ 3. 劇本管理 API

#### 3.1 獲取劇本列表
```bash
GET /api/v1/group-ai/scripts?skip=0&limit=20
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 列表查詢
- [ ] 搜索功能
- [ ] 篩選功能
- [ ] 緩存測試

#### 3.2 獲取劇本詳情
```bash
GET /api/v1/group-ai/scripts/{script_id}
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 詳情查詢
- [ ] 緩存測試

#### 3.3 創建劇本
```bash
POST /api/v1/group-ai/scripts
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "script_name": "test_script",
  "script_content": "yaml content here",
  "description": "test description"
}
```

**測試點**:
- [ ] 創建成功
- [ ] 緩存失效

#### 3.4 更新劇本
```bash
PUT /api/v1/group-ai/scripts/{script_id}
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 更新成功
- [ ] 緩存失效

#### 3.5 刪除劇本
```bash
DELETE /api/v1/group-ai/scripts/{script_id}
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 刪除成功
- [ ] 緩存失效

---

### ✅ 4. 監控 API

#### 4.1 儀表板統計
```bash
GET /api/v1/group-ai/dashboard/stats
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 返回統計數據
- [ ] 緩存測試

#### 4.2 系統指標
```bash
GET /api/v1/group-ai/monitor/metrics
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 返回系統指標
- [ ] 包含 CPU、內存等信息

#### 4.3 賬號指標
```bash
GET /api/v1/group-ai/monitor/accounts/metrics
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 返回賬號指標
- [ ] 緩存測試

---

### ✅ 5. 日誌 API

#### 5.1 獲取日誌列表
```bash
GET /api/v1/group-ai/logs?page=1&page_size=20&level=error
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 基本查詢
- [ ] 級別篩選（level）
- [ ] 搜索功能（q）
- [ ] 來源篩選（source）
- [ ] 時間範圍篩選（start_time, end_time）

#### 5.2 獲取日誌統計
```bash
GET /api/v1/group-ai/logs/statistics?hours=24
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] 返回統計數據
- [ ] 包含錯誤數量、級別分布等

#### 5.3 導出日誌
```bash
GET /api/v1/group-ai/logs/export?format=csv&level=error
Authorization: Bearer YOUR_TOKEN
```

**測試點**:
- [ ] CSV 導出
- [ ] JSON 導出

---

### ✅ 6. 健康檢查 API

#### 6.1 基礎健康檢查
```bash
GET /health
```

**預期響應**:
```json
{
  "status": "ok"
}
```

**測試點**:
- [ ] 無需認證
- [ ] 快速響應

#### 6.2 詳細健康檢查
```bash
GET /health?detailed=true
```

**預期響應**:
```json
{
  "status": "ok",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "cache": "healthy"
  }
}
```

**測試點**:
- [ ] 返回詳細信息
- [ ] 所有組件狀態

---

### ✅ 7. 緩存測試

#### 7.1 緩存命中測試
```bash
# 第一次請求（應該較慢）
time curl -X GET "https://aikz.usdt2026.cc/api/v1/group-ai/accounts" \
  -H "Authorization: Bearer $TOKEN"

# 第二次請求（應該很快，緩存命中）
time curl -X GET "https://aikz.usdt2026.cc/api/v1/group-ai/accounts" \
  -H "Authorization: Bearer $TOKEN"
```

**測試點**:
- [ ] 第一次請求時間 > 第二次請求時間
- [ ] 響應數據一致

#### 7.2 緩存失效測試
```bash
# 1. 獲取列表（緩存）
GET /api/v1/group-ai/accounts

# 2. 創建新賬號（應該清除緩存）
POST /api/v1/group-ai/accounts

# 3. 再次獲取列表（應該包含新賬號）
GET /api/v1/group-ai/accounts
```

**測試點**:
- [ ] 創建後列表包含新數據
- [ ] 緩存正確失效

---

## 🔍 性能測試

### 響應時間基準

| API 類型 | 首次請求 | 緩存命中 |
|---------|---------|---------|
| 列表 API | < 500ms | < 100ms |
| 詳情 API | < 300ms | < 50ms |
| 創建 API | < 1000ms | N/A |
| 更新 API | < 800ms | N/A |

### 並發測試

```bash
# 使用 Apache Bench 測試
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  https://aikz.usdt2026.cc/api/v1/group-ai/accounts
```

---

## 🐛 錯誤處理測試

### 常見錯誤場景

1. **401 Unauthorized**
   - 未提供 Token
   - Token 無效
   - Token 過期

2. **403 Forbidden**
   - 權限不足

3. **404 Not Found**
   - 資源不存在

4. **422 Unprocessable Entity**
   - 數據驗證失敗

5. **500 Internal Server Error**
   - 服務器錯誤

---

## 📊 測試結果記錄

### API 測試結果
- [ ] 認證 API: ✅ 通過 / ❌ 失敗
- [ ] 賬號管理 API: ✅ 通過 / ❌ 失敗
- [ ] 劇本管理 API: ✅ 通過 / ❌ 失敗
- [ ] 監控 API: ✅ 通過 / ❌ 失敗
- [ ] 日誌 API: ✅ 通過 / ❌ 失敗
- [ ] 健康檢查 API: ✅ 通過 / ❌ 失敗
- [ ] 緩存功能: ✅ 通過 / ❌ 失敗
- [ ] 性能: ✅ 通過 / ❌ 失敗

### 發現的問題
記錄所有 API 問題：
1. **端點**: 
2. **問題描述**: 
3. **請求**: 
4. **響應**: 
5. **預期**: 
6. **優先級**: 高/中/低

---

**最後更新**: 2025-12-09

