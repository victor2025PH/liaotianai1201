# Session Interaction Event Model 與互動接口設計

## 1. 整體架構
- **Session Interaction Service (SIS)**：管理 Session 帳號登入、群訊監聽與互動調度。
- **Redpacket Bot / 主系統**：維持遊戲邏輯、配置與獎勵結算。
- **中介層**：提供事件交換的統一路徑，可採 REST API 或 Message Queue（MQ）。

```
Redpacket Bot  <->  中介層 (REST / MQ)  <->  Session Interaction Service
                       |                         |
                       +-------> Session Client 1
                       +-------> Session Client 2
                               ...
```

## 2. 事件分類與資料結構

| 類型 | 發送方 | 接收方 | 說明 |
| ---- | ------ | ------ | ---- |
| `session.status` | SIS | Bot | 連線狀態改變（上線、離線、登入失敗） |
| `session.message` | SIS | Bot | Session 帳號讀到重要訊息（紅包觸發、使用者提問等） |
| `session.action` | Bot | SIS | 指示 Session 帳號執行動作（回覆、搶包、公告） |
| `redpacket.event` | Bot | SIS | 紅包遊戲相關事件（開始、更新、結束） |
| `ack` / `error` | 雙方 | 雙方 | 確認或錯誤回報 |

### 2.1 共通欄位
- `event_id`：UUID
- `timestamp`：ISO8601
- `source` / `target`：`bot` / `sis` / `session:<phone>`
- `payload`：JSON 內容

### 2.2 Payload 範例

**session.status**
```json
{
  "event_id": "uuid",
  "type": "session.status",
  "timestamp": "...",
  "source": "sis",
  "target": "bot",
  "payload": {
    "phone": "+8869...",
    "status": "ONLINE",
    "roles": ["player", "host"],
    "last_heartbeat_at": "..."
  }
}
```

**session.message**
```json
{
  "type": "session.message",
  "payload": {
    "phone": "+8869...",
    "chat_id": -100123456,
    "message_id": 12345,
    "text": "有人發紅包了！",
    "entities": [],
    "raw": { ... }
  }
}
```

**session.action**
```json
{
  "type": "session.action",
  "payload": {
    "action": "send_message",
    "phone": "+8869...",
    "chat_id": -100123456,
    "text": "恭喜大家準備搶紅包！",
    "reply_to_message_id": 12345,
    "metadata": {
      "strategy": "host_broadcast",
      "priority": "high"
    }
  }
}
```

**redpacket.event**
```json
{
  "type": "redpacket.event",
  "payload": {
    "event_id": "rp-20251112-001",
    "status": "START",
    "group_id": -100123456,
    "initiator": "+8869...",
    "amount": 88,
    "count": 6,
    "rules": {
      "strategy": "random",
      "deadline": "2025-11-12T10:00:00+08:00"
    }
  }
}
```

## 3. 介面形式與傳輸選型

### 3.1 REST API
- **適用**：快速 PoC、低頻指令。
- **接口示例**：
  - `POST /events/session`：SIS → Bot 報告事件。
  - `POST /events/actions`：Bot → SIS 下達指令。
  - `GET /sessions/status`：查詢帳號目前狀態。
- **優點**：實作簡單、無需新增基礎設施。
- **缺點**：缺少訊息重試與隊列機制，需要自行處理冪等與可靠性。

### 3.2 Message Queue（推薦）
- **選項**：RabbitMQ (AMQP)、Redis Streams、Kafka。
- **資料流**：
  - `queue/session_events`：SIS 發送。
  - `queue/action_commands`：Bot 發送。
  - `queue/acknowledge`：雙方回應。
- **優點**：天然支援重試、訂閱、多消費者；便於後續擴展。
- **缺點**：需部署 MQ，增加運維成本。

### 3.3 推薦方案
- 短期：緊湊時間可先使用 REST API，並在負責任務的端實作重試與冪等。
- 中期：切換至 RabbitMQ 或 Redis Streams，達成可用性、擴展性、監控需求。

## 4. Bot 與 SIS 的互動流程

1. **登入與狀態回報**
   - SIS 啟動 Session Client → 發送 `session.status` (ONLINE)。
   - Bot 更新帳號看板或通知營運。

2. **群訊監聽與事件上報**
   - Session Client 接收訊息 → 經策略判斷是否上報 → 透過 `session.message` 傳至 Bot。
   - Bot 可選擇存檔、分析、或觸發行動。

3. **紅包遊戲指令**
   - Bot 發送 `redpacket.event` → SIS 建立搶包任務。
   - SIS 按策略挑選帳號，透過 `session.action`（`grab_redpacket` / `send_message`）執行。
   - 搶包結果以 `session.message` 或 `session.status`（含 event payload）回傳。

4. **錯誤與告警**
   - 任何流程發生錯誤 → 發送 `error` 事件，包含 `event_id`、錯誤碼、描述。
   - 雙方收到後需記錄並視需求重試。

## 5. 對接注意事項
- **訊息冪等**：透過 `event_id` 確保重試不造成重複執行，必要時維護過去事件 cache。
- **安全驗證**：REST 可使用簽章 / token；MQ 建議設定使用者與 TLS。
- **節流調和**：Bot 下達指令時需檢查 Session 帳號的節流配置，防止超出頻率。
- **擴展性**：事件 model 須支援 `metadata` 欄位，以便後續添加新的策略或上下文。
- **監控追蹤**：所有事件應記錄於集中日誌與監控系統，方便追蹤與調試。

---

此文檔可作為 Week 2 「中介層事件模型與接口」的基礎，後續將依實作結果補充實際已實現的字段與錯誤碼範例。 

