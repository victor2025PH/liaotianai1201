# HTTP API 端點實現報告

> **完成日期**: 2025-01-XX  
> **狀態**: ✅ 會話和紅包服務 API 已完成

---

## 完成項目總覽

本次實現了兩個新的 HTTP API 服務模塊：

1. ✅ **會話服務 HTTP API** (`dialogue.py`)
2. ✅ **紅包服務 HTTP API** (`redpacket.py`)

---

## 詳細實現說明

### 1. ✅ 會話服務 HTTP API

**文件**: `admin-backend/app/api/group_ai/dialogue.py`

**實現的端點**:

#### 1.1 `GET /api/v1/group-ai/dialogue/contexts`
- **功能**: 獲取對話上下文列表
- **參數**:
  - `account_id` (可選): 賬號ID過濾
  - `group_id` (可選): 群組ID過濾
- **響應**: 對話上下文列表，包含歷史消息數、回復數、當前話題等

#### 1.2 `GET /api/v1/group-ai/dialogue/contexts/{account_id}/{group_id}`
- **功能**: 獲取指定賬號和群組的對話上下文
- **參數**:
  - `account_id`: 賬號ID
  - `group_id`: 群組ID
- **響應**: 單個對話上下文的詳細信息

#### 1.3 `GET /api/v1/group-ai/dialogue/history`
- **功能**: 獲取對話歷史
- **參數**:
  - `account_id`: 賬號ID（必需）
  - `group_id`: 群組ID（必需）
  - `limit`: 返回數量（默認 50，最大 200）
- **響應**: 對話歷史記錄列表，包含用戶和助手的所有消息

#### 1.4 `POST /api/v1/group-ai/dialogue/reply`
- **功能**: 手動觸發回復
- **請求體**:
  ```json
  {
    "account_id": "account_1",
    "group_id": -1001234567890,
    "message_text": "你好",
    "force_reply": false
  }
  ```
- **響應**: 回復文本或錯誤信息

**關鍵代碼**:
```python
@router.get("/contexts", response_model=List[DialogueContextResponse])
async def get_dialogue_contexts(...):
    """獲取對話上下文列表"""
    # 從 DialogueManager 獲取所有上下文
    # 支持按賬號和群組過濾

@router.post("/reply", response_model=ManualReplyResponse)
async def manual_reply(request: ManualReplyRequest, ...):
    """手動觸發回復"""
    # 創建模擬消息
    # 調用 DialogueManager.process_message
    # 支持強制回復（忽略回復率限制）
```

---

### 2. ✅ 紅包服務 HTTP API

**文件**: `admin-backend/app/api/group_ai/redpacket.py`

**實現的端點**:

#### 2.1 `GET /api/v1/group-ai/redpacket/stats`
- **功能**: 獲取紅包統計
- **參數**:
  - `account_id` (可選): 賬號ID過濾
  - `time_range_hours` (可選): 時間範圍（小時，1-168）
- **響應**: 紅包參與統計，包含總參與次數、成功率、總金額、平均金額等

#### 2.2 `GET /api/v1/group-ai/redpacket/history`
- **功能**: 獲取紅包參與歷史
- **參數**:
  - `account_id` (可選): 賬號ID過濾
  - `limit`: 返回數量（默認 100，最大 1000）
  - `time_range_hours` (可選): 時間範圍（小時，1-168）
- **響應**: 紅包參與歷史記錄列表

#### 2.3 `POST /api/v1/group-ai/redpacket/strategy`
- **功能**: 更新紅包參與策略
- **請求體**:
  ```json
  {
    "account_id": "account_1",  // 可選，None 表示更新默認策略
    "strategy_type": "composite",
    "strategy_params": {
      "sub_strategies": [
        {
          "type": "time_based",
          "params": {"peak_hours": [18, 19, 20]},
          "weight": 0.4
        },
        {
          "type": "amount_based",
          "params": {"min_amount": 0.01},
          "weight": 0.6
        }
      ]
    }
  }
  ```
- **支持的策略類型**:
  - `random`: 隨機策略
  - `time_based`: 時間策略
  - `amount_based`: 金額策略
  - `frequency`: 頻率策略
  - `composite`: 組合策略

#### 2.4 `GET /api/v1/group-ai/redpacket/hourly-count/{account_id}`
- **功能**: 獲取指定賬號當前小時的紅包參與次數
- **響應**: 當前計數、每小時上限、剩餘配額、是否達到上限

**關鍵代碼**:
```python
@router.get("/stats", response_model=RedpacketStatsResponse)
async def get_redpacket_stats(...):
    """獲取紅包統計"""
    # 從 RedpacketHandler 獲取統計
    # 支持按賬號和時間範圍過濾

@router.post("/strategy", response_model=StrategyUpdateResponse)
async def update_redpacket_strategy(request: StrategyUpdateRequest, ...):
    """更新紅包參與策略"""
    # 根據策略類型創建策略對象
    # 支持所有策略類型（包括組合策略）
```

---

## API 端點總覽

### 會話服務 API

| 方法 | 路徑 | 功能 |
|------|------|------|
| GET | `/api/v1/group-ai/dialogue/contexts` | 獲取對話上下文列表 |
| GET | `/api/v1/group-ai/dialogue/contexts/{account_id}/{group_id}` | 獲取指定對話上下文 |
| GET | `/api/v1/group-ai/dialogue/history` | 獲取對話歷史 |
| POST | `/api/v1/group-ai/dialogue/reply` | 手動觸發回復 |

### 紅包服務 API

| 方法 | 路徑 | 功能 |
|------|------|------|
| GET | `/api/v1/group-ai/redpacket/stats` | 獲取紅包統計 |
| GET | `/api/v1/group-ai/redpacket/history` | 獲取參與歷史 |
| POST | `/api/v1/group-ai/redpacket/strategy` | 更新參與策略 |
| GET | `/api/v1/group-ai/redpacket/hourly-count/{account_id}` | 獲取每小時計數 |

---

## 使用示例

### 1. 獲取對話上下文

```bash
# 獲取所有對話上下文
curl http://localhost:8000/api/v1/group-ai/dialogue/contexts

# 獲取指定賬號的對話上下文
curl http://localhost:8000/api/v1/group-ai/dialogue/contexts?account_id=account_1

# 獲取指定對話上下文
curl http://localhost:8000/api/v1/group-ai/dialogue/contexts/account_1/-1001234567890
```

### 2. 獲取對話歷史

```bash
curl "http://localhost:8000/api/v1/group-ai/dialogue/history?account_id=account_1&group_id=-1001234567890&limit=50"
```

### 3. 手動觸發回復

```bash
curl -X POST http://localhost:8000/api/v1/group-ai/dialogue/reply \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "account_1",
    "group_id": -1001234567890,
    "message_text": "你好",
    "force_reply": true
  }'
```

### 4. 獲取紅包統計

```bash
# 獲取所有賬號的統計
curl http://localhost:8000/api/v1/group-ai/redpacket/stats

# 獲取指定賬號的統計
curl http://localhost:8000/api/v1/group-ai/redpacket/stats?account_id=account_1

# 獲取最近24小時的統計
curl http://localhost:8000/api/v1/group-ai/redpacket/stats?time_range_hours=24
```

### 5. 獲取紅包歷史

```bash
curl "http://localhost:8000/api/v1/group-ai/redpacket/history?account_id=account_1&limit=100&time_range_hours=24"
```

### 6. 更新紅包策略

```bash
# 更新默認策略為時間策略
curl -X POST http://localhost:8000/api/v1/group-ai/redpacket/strategy \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_type": "time_based",
    "strategy_params": {
      "peak_hours": [18, 19, 20, 21],
      "peak_probability": 0.8,
      "off_peak_probability": 0.3
    }
  }'

# 更新指定賬號的策略為組合策略
curl -X POST http://localhost:8000/api/v1/group-ai/redpacket/strategy \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "account_1",
    "strategy_type": "composite",
    "strategy_params": {
      "sub_strategies": [
        {
          "type": "time_based",
          "params": {"peak_hours": [18, 19, 20]},
          "weight": 0.4
        },
        {
          "type": "amount_based",
          "params": {"min_amount": 0.01},
          "weight": 0.6
        }
      ]
    }
  }'
```

### 7. 獲取每小時計數

```bash
curl http://localhost:8000/api/v1/group-ai/redpacket/hourly-count/account_1
```

---

## 響應格式示例

### 對話上下文響應

```json
{
  "account_id": "account_1",
  "group_id": -1001234567890,
  "history_count": 15,
  "last_reply_time": "2025-01-XX 14:30:00",
  "reply_count_today": 5,
  "current_topic": "聊天",
  "mentioned_users": [123456789, 987654321]
}
```

### 對話歷史響應

```json
{
  "account_id": "account_1",
  "group_id": -1001234567890,
  "history": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": "2025-01-XX 14:30:00",
      "message_id": 123,
      "user_id": 123456789
    },
    {
      "role": "assistant",
      "content": "你好！很高興認識你",
      "timestamp": "2025-01-XX 14:30:01"
    }
  ],
  "total_count": 15
}
```

### 紅包統計響應

```json
{
  "account_id": "account_1",
  "total_participations": 50,
  "successful": 45,
  "failed": 5,
  "success_rate": 0.9,
  "total_amount": 250.5,
  "average_amount": 5.57,
  "time_range": "24小時"
}
```

### 紅包歷史響應

```json
{
  "account_id": "account_1",
  "history": [
    {
      "redpacket_id": "redpacket_123",
      "account_id": "account_1",
      "success": true,
      "amount": 5.5,
      "error": null,
      "timestamp": "2025-01-XX 14:30:00"
    }
  ],
  "total_count": 50,
  "time_range": "24小時"
}
```

---

## 修改文件清單

1. `admin-backend/app/api/group_ai/dialogue.py` - 新建會話服務 API
2. `admin-backend/app/api/group_ai/redpacket.py` - 新建紅包服務 API
3. `admin-backend/app/api/group_ai/__init__.py` - 註冊新路由

---

## 錯誤處理

所有 API 端點都包含完整的錯誤處理：

- **404 Not Found**: 資源不存在（如賬號、上下文）
- **400 Bad Request**: 請求參數錯誤
- **500 Internal Server Error**: 服務器內部錯誤
- **503 Service Unavailable**: 服務未初始化

所有錯誤都包含詳細的錯誤信息，便於調試。

---

## 測試建議

### 1. 會話服務 API 測試

```bash
# 測試獲取對話上下文
curl http://localhost:8000/api/v1/group-ai/dialogue/contexts

# 測試手動觸發回復
curl -X POST http://localhost:8000/api/v1/group-ai/dialogue/reply \
  -H "Content-Type: application/json" \
  -d '{"account_id": "test_account", "group_id": -1001234567890, "message_text": "測試"}'
```

### 2. 紅包服務 API 測試

```bash
# 測試獲取統計
curl http://localhost:8000/api/v1/group-ai/redpacket/stats

# 測試更新策略
curl -X POST http://localhost:8000/api/v1/group-ai/redpacket/strategy \
  -H "Content-Type: application/json" \
  -d '{"strategy_type": "random", "strategy_params": {"base_probability": 0.7}}'
```

---

## 後續優化建議

### 短期（1週內）

- [ ] 添加 API 文檔（Swagger/OpenAPI）
- [ ] 添加請求驗證和參數校驗
- [ ] 添加 API 速率限制

### 中期（2-4週）

- [ ] 實現 WebSocket 實時推送（監控指標）
- [ ] 添加 API 認證和授權
- [ ] 實現 API 版本控制

### 長期（1-2個月）

- [ ] 添加 API 監控和日誌
- [ ] 實現 API 緩存機制
- [ ] 添加 API 性能優化

---

## 總結

本次實現了會話服務和紅包服務的完整 HTTP API，包括：

1. **會話服務 API**: 4個端點，支持獲取上下文、歷史和手動觸發回復
2. **紅包服務 API**: 4個端點，支持統計、歷史、策略更新和每小時計數
3. **完整的錯誤處理**: 所有端點都有適當的錯誤處理
4. **靈活的參數**: 支持過濾、分頁、時間範圍等

所有 API 已集成到現有路由系統，可以通過 `/api/v1/group-ai/dialogue/...` 和 `/api/v1/group-ai/redpacket/...` 訪問。

---

**狀態**: ✅ 會話和紅包服務 HTTP API 實現完成，可以投入使用

