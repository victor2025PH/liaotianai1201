# API 端點驗證完整指南

> **日期**: 2025-12-01  
> **任務**: 本週任務 1 - API 端點驗證

---

## 📋 驗證目標

測試以下 API 端點的完整功能：

1. ✅ 認證登錄 API
2. ✅ 劇本管理 API
3. ✅ 賬號管理 API
4. ✅ Worker 管理 API
5. ✅ 服務器管理 API
6. ✅ 監控 API
7. ✅ 儀表板 API

---

## 🔑 默認登錄憑據

根據代碼分析：

- **用戶名**: `admin@example.com`
- **密碼**: `changeme123`
- **登錄端點**: `POST /api/v1/auth/login`

---

## 🚀 快速驗證（推薦）

在服務器終端執行以下完整驗證腳本：

```bash
cd ~/liaotian && \
chmod +x deploy/API端点完整验证.sh && \
bash deploy/API端点完整验证.sh
```

---

## 📋 手動執行步驟

### 步驟 1: 獲取認證 Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123"
```

**預期響應**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

保存 Token 到變量：
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token: ${TOKEN:0:50}..."
```

---

### 步驟 2: 測試關鍵 API 端點

#### 2.1 劇本列表 API

```bash
curl -X GET http://localhost:8000/api/v1/group-ai/scripts/ \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.2 賬號列表 API

```bash
curl -X GET http://localhost:8000/api/v1/group-ai/accounts/ \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.3 Worker 列表 API

```bash
curl -X GET http://localhost:8000/api/v1/workers \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.4 服務器列表 API

```bash
curl -X GET http://localhost:8000/api/v1/group-ai/servers/ \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.5 監控指標 API

```bash
curl -X GET http://localhost:8000/api/v1/group-ai/monitor/metrics \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.6 儀表板統計 API

```bash
curl -X GET http://localhost:8000/api/v1/group-ai/dashboard/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 完整驗證命令（一行）

```bash
cd ~/liaotian && \
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4) && \
echo "Token 獲取: $([ -n "$TOKEN" ] && echo "成功" || echo "失敗")" && \
echo "" && \
echo "測試關鍵 API..." && \
echo "1. 劇本 API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/scripts/)" && \
echo "2. 賬號 API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/accounts/)" && \
echo "3. Worker API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/workers)" && \
echo "4. 服務器 API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/servers/)" && \
echo "=== 驗證完成 ==="
```

---

## ✅ 預期結果

### 成功情況

- ✅ 登錄成功，獲取 Token
- ✅ 所有 API 返回 HTTP 200
- ✅ JSON 響應正常

### 需要處理的情況

- ⚠️ Token 獲取失敗：需要檢查用戶是否存在或密碼是否正確
- ⚠️ API 返回 401：Token 無效或過期
- ⚠️ API 返回 404：端點不存在

---

**執行驗證命令，告訴我結果！**
