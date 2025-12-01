# 服務器上直接執行 API 驗證（無需文件）

> **日期**: 2025-12-01  
> **任務**: API 端點驗證

---

## 🚀 立即執行（複製粘貼）

在服務器終端執行以下完整驗證：

```bash
cd ~/liaotian && \
echo "=========================================" && \
echo "API 端點完整驗證" && \
echo "=========================================" && \
echo "" && \
echo "【步驟 1】獲取認證 Token..." && \
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123") && \
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4) && \
if [ -z "$TOKEN" ]; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data=sys.stdin.read(); obj=json.loads(data) if data.strip().startswith('{') else {}; print(obj.get('access_token', ''))" 2>/dev/null || echo "")
fi && \
if [ -n "$TOKEN" ]; then
    echo "✓ Token 獲取成功"
    echo "Token 前50字符: ${TOKEN:0:50}..."
else
    echo "✗ Token 獲取失敗"
    echo "響應: $LOGIN_RESPONSE" | head -5
fi && \
echo "" && \
if [ -n "$TOKEN" ]; then
    echo "【步驟 2】測試關鍵 API 端點..." && \
    echo "" && \
    echo "1. 劇本列表 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/scripts/ && \
    echo "" && \
    echo "2. 賬號列表 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/accounts/ && \
    echo "" && \
    echo "3. Worker 列表 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/workers && \
    echo "" && \
    echo "4. 服務器列表 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/servers/ && \
    echo "" && \
    echo "5. 儀表板統計 API:" && \
    curl -s -o /dev/null -w "   HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/dashboard/stats && \
    echo ""
fi && \
echo "=========================================" && \
echo "驗證完成" && \
echo "========================================="
```

---

## 📋 分步執行（如果上面的命令太長）

### 步驟 1: 登錄並獲取 Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123"
```

保存 Token：
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token: ${TOKEN:0:50}..."
```

### 步驟 2: 測試 API 端點

```bash
# 劇本列表
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/scripts/ | head -10

# 賬號列表
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/accounts/ | head -10

# Worker 列表
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/workers | head -10
```

---

**執行驗證命令，告訴我結果！**
