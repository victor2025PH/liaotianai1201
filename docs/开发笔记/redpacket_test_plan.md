# 紅包遊戲端到端測試計畫（Week 3）

## 1. 目標
- 驗證 Session Interaction Service（SIS）與紅包 Bot 之整體流程：紅包啟動、Session 帳號參與、結果公告。
- 模擬至少 5 個 Session 帳號、3 場紅包遊戲，確認搶包延遲、成功率、異常應對等指標。
- 提供測試報告模板以利週末評審會議與後續迭代優化。

## 2. 測試環境
- Telegram 測試群組 `@sandbox_redpacket`（私有群，包含 Bot、5+ Session 帳號）。
- Session 帳號：Host 1 名、Player 4 名（可視情況增加備援帳號）。
- 服務啟動：
  - Redpacket Bot：若為本地端，啟動 `python bot_redpacket.py --config configs/stage.yaml`
  - SIS：啟動 `python session_service/run.py --env stage`（待綁定實作），或分別啟動 `session_pool`, `dispatch`, `actions`.
- Logging：`logs/session_service.log`、`logs/redpacket_bot.log`；若有監控，確保 Prometheus/Grafana 已接收到指標。

## 3. 測試場景

### 3.1 基線流程（場次 A）
1. 啟動紅包事件（透過管理後台或 Bot 指令 `#start_redpacket amount count`）。
2. 確認 SIS 收到 `redpacket.event`，主持帳號宣布開始。
3. 玩家 Session 帳號搶包（目前模擬為 action log）。
4. Bot 宣布結果 → SIS 轉發到群組。
5. 紀錄耗時與結果。

### 3.2 高併發流程（場次 B）
1. 同時啟動 2-3 個紅包事件（間隔 ≤ 5 秒）。
2. 觀察 SIS 節流行為、FloodWait 重試與重試次數。
3. 比對每次搶包耗時（觸發→SIS處理→結果）。
4. 確認未出現 crash 或長時間阻塞。

### 3.3 異常處理流程（場次 C）
1. 模擬 session 遭遇 FloodWait（透過降低節流參數或高頻送訊）。
2. 手動禁用某個帳號（將其 status 設為 `SUSPENDED`），確認 SIS 會跳過並使用備援帳號。
3. 模擬 Bot 發送錯誤事件（缺少欄位）並觀察 SIS 錯誤回報。

## 4. 測試步驟（示例）
1. 準備
   - 確認所有 Session 帳號已登入並在線（透過 `account_status.py`）。
   - 啟用 Bot 與 SIS，確認日誌無錯誤。
2. 場次執行
   - 根據上方流程執行 A/B/C 三場。
   - 每場紀錄以下資訊：
     - 發放時間、紅包 ID、群組 ID。
     - Session 回覆 / 公告時間。
     - 消息量與 FloodWait 日誌。
     - 成功率（參與帳號 / 目標帳號）。
3. 數據收集
   - 匯整 `logs/` 中對應段落，記錄告警或錯誤事件。
   - 若整合監控，匯出 Prometheus 指標（API 錯誤、延遲）。

## 5. 結果評估指標
- **響應延遲**：紅包觸發到 Session 帳號公告開始的時間 < 2 秒；公布結果 < 5 秒。
- **成功率**：目標玩家均收到並（模擬）完成搶包操作；若為真實操作，需人工確認 Telegram UI。
- **錯誤處理**：FloodWait 或 API 錯誤應被捕捉並重試；日誌無未處理例外。
- **穩定性**：SIS 無崩潰；CPU / 記憶體資源穩定；重試不會造成非預期請求。

## 6. 報告模板

| 場次 | 啟動時間 | 紅包 ID | 參與帳號 | 平均響應延遲 | FloodWait 次數 | 成功率 | 備註 |
| ---- | -------- | ------- | -------- | ------------- | --------------- | ------- | ---- |
| A 基線 | | | | | | | |
| B 高併發 | | | | | | | |
| C 異常 | | | | | | | |

補充：
- 日誌摘要（重要事件、錯誤）。
- 可改進項目（例如節流參數調整建議、市場使用者體驗建議）。

---

此計畫文件用於指導 Week 3 w3-task4 的端到端測試與報告整理，可於執行後直接填寫結果並提交評審。 

