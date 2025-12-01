# 查看實際 API 響應數據

> **日期**: 2025-12-01

---

## 🚀 查看實際 API 響應（完整命令）

在服務器終端執行：

```bash
# 獲取 Token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123" | \
  python3 -c "import sys, json; print(json.loads(sys.stdin.read()).get('access_token', ''))")

echo "=========================================" && \
echo "查看 API 實際響應數據" && \
echo "=========================================" && \
echo "" && \
echo "【1】劇本列表（前3個）..." && \
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/scripts/?limit=3" | python3 -m json.tool 2>/dev/null | head -40 || \
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/scripts/?limit=3" && \
echo "" && \
echo "" && \
echo "【2】賬號列表（前3個）..." && \
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/accounts/?limit=3" | python3 -m json.tool 2>/dev/null | head -40 || \
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/accounts/?limit=3" && \
echo "" && \
echo "" && \
echo "【3】服務器列表..." && \
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/servers/" | python3 -m json.tool 2>/dev/null | head -40 || \
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/servers/" && \
echo "" && \
echo "" && \
echo "【4】Worker 列表（修正路徑）..." && \
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/workers/" | python3 -m json.tool 2>/dev/null | head -40 || \
curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/workers/" && \
echo "" && \
echo "" && \
echo "【5】儀表板統計（修正路徑）..." && \
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/dashboard/" | python3 -m json.tool 2>/dev/null | head -40 || \
curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/dashboard/" && \
echo "" && \
echo "=========================================" && \
echo "完成" && \
echo "========================================="
```

---

**執行命令查看實際響應數據！**
