# 監控告警與上線報告指南

## 1. 監控指標

### 1.1 核心指標
| 指標 | 說明 | 來源 |
| --- | --- | --- |
| `session_online_count` | 當前在線 Session 帳號數量 | Session Client Pool |
| `session_event_latency_seconds` | SIS 處理事件耗時 | 中介層或事件處理器 |
| `dispatch_floodwait_total` | FloodWait 遭遇次數 | DispatchManager |
| `redpacket_success_count` | 紅包搶包成功次數 | RedpacketEventProcessor |
| `redpacket_failure_count` | 搶包失敗 / 異常次數 | RedpacketEventProcessor |
| `action_retry_total` | SessionActionExecutor 重試次數 | 行動執行器 |

### 1.2 系統資源
- CPU、記憶體、網路流量：Docker / systemd 監控工具，或透過 Prometheus Node Exporter。
- Redis / PostgreSQL 指標（若使用）：連線數、Memory 使用、慢查詢。

### 1.3 Prometheus Exporter（範例）
- 實作 `metrics.py` 暴露 `/metrics`（可使用 `prometheus_client`）。
- 範例：
  ```python
  from prometheus_client import Counter, Gauge, Histogram

  session_online_count = Gauge("session_online_count", "Number of online session accounts")
  dispatch_floodwait_total = Counter("dispatch_floodwait_total", "Total FloodWait occurrences")
  session_event_latency = Histogram("session_event_latency_seconds", "Latency for handling events")
  ```
- Docker Compose 可加入 `prometheus.yml`與 `grafana`, 重用現有監控平台。

## 2. 告警設定

### 2.1 閾值建議
- `session_online_count < 授權帳號 80%` → 發送告警（Signal: Slack or Telegram Bot）
- `dispatch_floodwait_total` 1 分鐘內 > 10 次 → 提醒調整節流。
- `redpacket_failure_count` 連續發生 3 次 → 需人工介入。
- CPU > 80%、記憶體 > 70% 持續 10 分鐘 → 警告。

### 2.2 告警通道
- **Telegram**：自建告警 Bot，透過 API 送出訊息。
- **Slack**：Incoming Webhook。
- **Email**：使用 SES / SendGrid。
預設優先使用 Telegram + Slack。

### 2.3 實作建議
- 在 `session_service` 中集成告警模組（如 `alerts.py`），當捕捉到異常事件時發送通知。
- 設計簡單的 `AlertManager`，支援批次告警與冷卻時間，避免通知轟炸。

## 3. 上線報告模板

### 3.1 基本資訊
| 項目 | 內容 |
| --- | --- |
| 上線日期 | YYYY-MM-DD |
| 負責人 |  |
| 版本 / Commit |  |
| 相關任務 | Week 4 任務清單 |

### 3.2 測試總結
| 類型 | 狀態 | 說明 |
| --- | --- | --- |
| 單元測試 | ✅/⚠️ | |
| 自動化測試 | ✅/⚠️ | `pytest tests/...` |
| 壓力測試 | ✅/⚠️ | 設定、結果 |
| 紅包端到端 | ✅/⚠️ | 場次 A/B/C 成果 |

### 3.3 監控配置摘要
- Prometheus / Grafana Dashboard URL
- 告警通道：Telegram `@ops_alert`, Slack channel `#sis-alert`
- 告警規則（簡述）

### 3.4 風險與緩解
- **風險 1**：Session 過期 → 告警 + CLI 重登 SOP。
- **風險 2**：FloodWait 過多 → 調整節流參數、增加備援帳號。
- **風險 3**：Bot API 變動 → 預留備援 Bot / 回滾機制。

### 3.5 後續優化建議
- 增加紅包搶包真實模擬（Bandwith / 可靠性測試）。
- 架構分層監控面板（Session 與 Redpacket 指標）。
- 自動化部署（CI/CD）整合。

## 4. 上線流程
1. 確認所有測試（單元 + 自動化 + 壓力 + 端到端）已通過，並更新報告。
2. 啟用監控與告警，驗證通知孔道。
3. 執行部署（Docker / systemd），觀察 30 分鐘。
4. 填寫上線報告並通過評審會議。
5. 進入運營觀察期（至少 24 小時），評估是否要切換至後續迭代項目。

---

此指南支援 Week 4 最終交付，可隨日後擴充或調整告警策略。 

