# 紅包遊戲 API 配置文檔

> 更新時間：2025-12-03

---

## 🌐 測試環境配置

### API 基本信息

```
API 地址: https://api.usdt2026.cc/api/v2/ai
API Key:  test-key-2024
```

### 認證方式

**Headers:**
- `Authorization: Bearer test-key-2024`
- `X-Telegram-User-Id: <用戶的Telegram ID>`

### 測試用戶

```
Telegram ID: 5433982810
當前餘額: 9988.706 USDT
```

---

## 📡 可用端點

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/v2/ai/status` | 健康檢查 |
| GET | `/api/v2/ai/wallet/balance` | 查詢餘額 |
| GET | `/api/v2/ai/user/profile` | 用戶資料 |
| POST | `/api/v2/ai/packets/send` | 發送紅包 |
| POST | `/api/v2/ai/packets/claim` | 領取紅包 |
| POST | `/api/v2/ai/wallet/transfer` | 內部轉帳 |
| GET | `/api/v2/ai/packets/{uuid}` | 紅包詳情 |

---

## 🧪 測試命令

### 查詢餘額

```bash
curl -s "https://api.usdt2026.cc/api/v2/ai/wallet/balance" \
  -H "Authorization: Bearer test-key-2024" \
  -H "X-Telegram-User-Id: 5433982810"
```

### 健康檢查

```bash
curl -s "https://api.usdt2026.cc/api/v2/ai/status" \
  -H "Authorization: Bearer test-key-2024"
```

### 發送紅包

```bash
curl -X POST "https://api.usdt2026.cc/api/v2/ai/packets/send" \
  -H "Authorization: Bearer test-key-2024" \
  -H "X-Telegram-User-Id: 5433982810" \
  -H "Content-Type: application/json" \
  -d '{
    "total_amount": 10.0,
    "total_count": 5,
    "currency": "usdt",
    "packet_type": "random",
    "message": "🤖 AI 紅包"
  }'
```

### 領取紅包

```bash
curl -X POST "https://api.usdt2026.cc/api/v2/ai/packets/claim" \
  -H "Authorization: Bearer test-key-2024" \
  -H "X-Telegram-User-Id: 5433982810" \
  -H "Content-Type: application/json" \
  -d '{
    "packet_uuid": "紅包UUID"
  }'
```

---

## ⚙️ 後端配置

### 在網頁上配置

1. 訪問：`https://aikz.usdt2026.cc/group-ai/redpacket`
2. 填寫配置：
   - **API 地址**: `https://api.usdt2026.cc/api/v2/ai`
   - **API Key**: `test-key-2024`
   - **啟用**: ✅
3. 點擊「保存配置」
4. 點擊「測試連接」驗證

### 通過 API 配置

```bash
curl -X POST "https://aikz.usdt2026.cc/api/v1/redpacket/config" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "api_url": "https://api.usdt2026.cc/api/v2/ai",
    "api_key": "test-key-2024",
    "enabled": true
  }'
```

---

## 🔧 Worker 節點配置

### 環境變量（可選）

```bash
# 在 Worker 部署包中設置
export REDPACKET_API_URL="https://api.usdt2026.cc/api/v2/ai"
export REDPACKET_API_KEY="test-key-2024"
```

### Excel 配置（推薦）

在 Excel 配置文件中添加列：

| phone | api_id | api_hash | redpacket_enabled | ... |
|-------|--------|----------|------------------|-----|
| 639277358115 | 30390800 | 471481... | 1 | ... |

---

## 📝 注意事項

1. **API 地址格式**：確保使用完整路徑 `https://api.usdt2026.cc/api/v2/ai`，不要加尾隨斜杠
2. **Telegram User ID**：必須是數字格式，如 `5433982810`
3. **認證 Headers**：兩個 Header 都必須提供
4. **測試環境**：當前為測試環境，生產環境配置可能不同

---

## 🔄 下一步

1. ✅ 配置後端 API
2. ✅ 測試連接
3. ⏳ 在 Worker 中集成紅包 SDK
4. ⏳ 實現自動發/搶紅包功能
5. ⏳ 實現消息監聽和觸發

---

*文檔更新時間：2025-12-03*
