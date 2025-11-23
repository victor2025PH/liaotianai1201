# Session Interaction Service 架構設計

## 1. 系統概覽
- **目的**：管理多個 Telegram Session 帳號登入、監聽與互動，支援紅包遊戲參與與群聊回覆。
- **範圍**：僅處理 Session 帳號層的登入維運與互動調度；遊戲規則與統計由既有紅包 Bot 負責。
- **依賴**：Pyrogram / Telethon、PostgreSQL(or aiosqlite for PoC)、Redis、FastAPI / aiohttp。

## 2. 模組劃分
1. **Session Manager**
   - 登入 / 登出 / 心跳檢測
   - Session 檔加密解密、儲存路徑管理
   - 帳號狀態更新（上線、離線、需重登）
2. **Account Registry API**
   - REST/GraphQL 介面 (FastAPI)
   - 查詢帳號狀態、啟停帳號、調整節流參數
3. **Event Listener**
   - 使用 Client 監聽群組訊息 (`on_message`)
   - 將事件發送至 Message Bus / Redis Stream
4. **Interaction Orchestrator**
   - 基於策略（輪詢、權重、主持名單）指派帳號回覆 / 搶包
   - 控制節流：per-account、per-group、global QPS
5. **Command Processor**
   - 解析來自紅包 Bot 或營運後台的指令（啟動紅包、公告、提醒）
   - 透過 Orchestrator 執行，並回傳執行情況
6. **Monitoring & Alerting**
   - 收集指標：登入率、訊息延遲、API 錯誤碼
   - 整合 Prometheus 指標、通知 Slack / TG

## 3. 資料模型
### 3.1 資料表
```text
accounts
  id (uuid)
  phone_number
  display_name
  session_path
  status (ACTIVE / OFFLINE / NEED_RELOGIN / SUSPENDED)
  roles (player, host, helper)
  throttle_profile (json)
  last_heartbeat_at
  created_at, updated_at

account_logs
  id
  account_id -> accounts.id
  event (LOGIN_SUCCESS, LOGIN_FAILED, RATE_LIMITED, REDPACKET_SUCCESS, etc.)
  payload jsonb
  created_at

group_profiles
  group_id
  name
  strategies jsonb   // 回覆策略、紅包參與策略
  last_active_at

redpacket_events
  id
  group_id
  initiator_account_id
  payload jsonb
  status (INIT, RUNNING, COMPLETED, FAILED)
  created_at, updated_at
```

### 3.2 Redis Keys（示意）
- `sis:account:{id}:rate_limit`
- `sis:group:{group_id}:pending_tasks`
- `sis:redpacket:{event_id}:state`

## 4. 時序流程
1. **登入流程**  
   CLI 生成 `.session` → 透過 REST API 註冊 → Session Manager 加入帳號池 → Scheduler 嘗試登入 → 更新 `accounts.status`。
2. **群訊監聽**  
   Event Listener → 解析訊息 → 發送到 `sis:group:{group_id}:pending_tasks` → Orchestrator 消費 → 決定回覆帳號 → 呼叫 `client.send_message`。
3. **紅包事件**  
   紅包 Bot 發送事件至 Message Bus → Command Processor 收到 → 創建 `redpacket_events` → Orchestrator 指派 Session 帳號 → 搶包結果回報 → Bot 更新排行榜。

## 5. 安全與節流
- Session 文件儲存在 `sessions/`，使用 AES-256-GCM + master key（環境變數或 Vault）。
- 單帳號與全域節流：配置 `Burst` + `Rate`，避免觸發 420/429。
- 日誌去識別化（電話、群 ID hashing）。
- 定期檢查 IP 白名單與兩步驗證狀態。

## 6. 技術棧與工具選型
- **語言**：Python 3.11+
- **框架**：Pyrogram（優先）/ Telethon（備援）
- **HTTP API**：FastAPI
- **資料庫**：PostgreSQL（生產）/ SQLite（開發 PoC）
- **快取 / 佇列**：Redis（Stream / PubSub）
- **部署**：Docker + docker-compose；CI 使用 GitHub Actions
- **監控**：Prometheus + Grafana / Loki

## 7. 開發與部署注意事項
- 先以 3~5 帳號測試，逐步擴展至 10+，觀察限流情況。
- 生產時建議多區域 IP 代理組合，降低同 IP 多帳號風險。
- 指令與回覆策略需可配置（透過 DB 或 YAML），便於營運調整。
- 保留手動介面（後台或 CLI）可暫停 / 啟動帳號，以應對突發情況。

---

此設計文件作為 Week 1 的起始藍圖，後續會依實作結果和營運反饋更新細節。 

