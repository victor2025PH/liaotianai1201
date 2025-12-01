# 立即執行 API 驗證 - 服務器命令

> **日期**: 2025-12-01  
> **用途**: 直接在服務器上執行 API 驗證

---

## 🚀 執行 API 驗證（複製粘貼）

在服務器終端執行以下命令：

```bash
cd ~/liaotian && \
echo "=========================================" && \
echo "API 端點完整驗證" && \
echo "=========================================" && \
echo "" && \
echo "【步驟 1】登錄獲取 Token..." && \
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123") && \
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; d=sys.stdin.read(); j=json.loads(d) if d.strip().startswith('{') else {}; print(j.get('access_token', ''))" 2>/dev/null) && \
if [ -n "$TOKEN" ]; then
    echo "✓ 登錄成功，Token 獲取成功"
    echo "Token 前50字符: ${TOKEN:0:50}..."
else
    echo "✗ Token 獲取失敗"
    echo "響應: $LOGIN_RESPONSE"
    echo "繼續測試公共端點..."
fi && \
echo "" && \
echo "【步驟 2】測試關鍵 API 端點..." && \
if [ -n "$TOKEN" ]; then
    echo "1. 劇本列表 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/scripts/" && \
    echo "" && \
    echo "2. 賬號列表 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/accounts/" && \
    echo "" && \
    echo "3. Worker 列表 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/workers" && \
    echo "" && \
    echo "4. 服務器列表 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/servers/" && \
    echo "" && \
    echo "5. 儀表板統計 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/dashboard/stats" && \
    echo "" && \
    echo "【步驟 3】查看實際響應（劇本列表前5個）..." && \
    curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/scripts/?limit=5" | python3 -m json.tool 2>/dev/null | head -30 || \
    curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/scripts/?limit=5" | head -10
else
    echo "⚠ 無 Token，測試端點是否存在（會返回 401）..." && \
    echo "  劇本 API: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/group-ai/scripts/)" && \
    echo "  賬號 API: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/group-ai/accounts/)" && \
    echo "  Worker API: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/workers)"
fi && \
echo "" && \
echo "=========================================" && \
echo "驗證完成" && \
echo "========================================="
```

---

## 📋 簡化版本（分步執行）

### 步驟 1: 登錄

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123"
```

### 步驟 2: 保存 Token 並測試

```bash
# 保存 Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" | \
  python3 -c "import sys, json; print(json.loads(sys.stdin.read()).get('access_token', ''))")

# 測試 API
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/scripts/ | head -10
```

---

## ✅ 預期結果

### 成功情況

- ✅ Token 獲取成功
- ✅ 所有 API 返回 HTTP 200
- ✅ JSON 響應正常

### 需要處理

- ⚠️ 登錄失敗：可能需要創建管理員用戶
- ⚠️ API 返回 401：Token 無效
- ⚠️ API 返回 404：端點不存在

---

**執行驗證命令，告訴我結果！**
