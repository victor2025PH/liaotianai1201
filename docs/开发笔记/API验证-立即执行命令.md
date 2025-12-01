# API 驗證 - 立即執行命令

> **日期**: 2025-12-01

---

## 🚀 快速驗證（複製粘貼）

在服務器終端執行：

```bash
echo "=== API 端點驗證 ===" && \
echo "" && \
echo "【1】登錄獲取 Token..." && \
LOGIN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=changeme123") && \
TOKEN=$(echo "$LOGIN" | python3 -c "import sys, json; d=sys.stdin.read(); print(json.loads(d).get('access_token', '')) if d.strip().startswith('{') else ''" 2>/dev/null || echo "") && \
if [ -n "$TOKEN" ]; then
    echo "✓ Token 獲取成功" && \
    echo "" && \
    echo "【2】測試 API 端點..." && \
    echo "  劇本 API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/scripts/)" && \
    echo "  賬號 API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/accounts/)" && \
    echo "  Worker API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/workers)" && \
    echo "  服務器 API: $(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/group-ai/servers/)" && \
    echo "" && \
    echo "【3】查看劇本列表（前3個）..." && \
    curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/group-ai/scripts/?limit=3" | python3 -m json.tool 2>/dev/null | head -20 || echo "響應格式檢查中..."
else
    echo "✗ Token 獲取失敗" && \
    echo "響應: $LOGIN"
fi && \
echo "" && \
echo "=== 驗證完成 ==="
```

---

## 📋 默認登錄憑據

- **用戶名**: `admin@example.com`
- **密碼**: `changeme123`
- **端點**: `POST /api/v1/auth/login`

---

**執行命令，告訴我結果！**
