# 監控與告警檢查清單

本文檔列出關鍵監控指標、告警閾值和排查思路。

---

## 關鍵監控指標

### 1. API 錯誤率

| 指標 | 說明 | 關注點 / 建議閾值 | 告警產生後的排查思路 |
|------|------|-----------------|-------------------|
| `api_error_rate` | API 請求錯誤率（4xx + 5xx / 總請求數） | **警告**：> 1%<br>**嚴重**：> 5% | 1. 檢查後端日誌（`admin-backend` 日誌）<br>2. 查看具體錯誤類型（4xx 通常是參數錯誤，5xx 是服務器錯誤）<br>3. 檢查數據庫連接（`DATABASE_URL`）<br>4. 檢查 Redis 連接（`REDIS_URL`）<br>5. 檢查外部服務（`SESSION_SERVICE_URL` 等）<br>6. 查看 `saas-demo` 前端 Network 面板，確認具體失敗的 API 端點 |

**監控位置**：
- Prometheus：`admin-backend/prometheus.yml`
- 後端日誌：`admin-backend` 容器日誌或終端輸出
- 前端界面：`http://localhost:3000/monitoring`

### 2. API 響應時間

| 指標 | 說明 | 關注點 / 建議閾值 | 告警產生後的排查思路 |
|------|------|-----------------|-------------------|
| `api_response_time_p95` | 95% 分位數響應時間 | **警告**：> 1000ms<br>**嚴重**：> 3000ms | 1. 檢查數據庫查詢性能（慢查詢日誌）<br>2. 檢查外部 API 調用（`data_sources.py` 中的 HTTP 請求）<br>3. 檢查 Redis 連接延遲<br>4. 檢查服務器資源（CPU、內存）<br>5. 查看 `saas-demo` Dashboard 的響應時間趨勢圖 |

**監控位置**：
- 後端：`/api/v1/metrics` 端點返回的 `response_time.average`
- 前端：`http://localhost:3000/` Dashboard 響應時間趨勢圖
- Prometheus：可通過 Histogram 指標監控

### 3. 會話創建失敗數

| 指標 | 說明 | 關注點 / 建議閾值 | 告警產生後的排查思路 |
|------|------|-----------------|-------------------|
| `session_create_failure_count` | 會話創建失敗次數（1 分鐘內） | **警告**：> 3 次<br>**嚴重**：> 10 次 | 1. 檢查 `session_service/` 日誌<br>2. 檢查 Telegram API 連接（`TELEGRAM_API_ID`、`TELEGRAM_API_HASH`）<br>3. 檢查會話文件是否有效（`TELEGRAM_SESSION_FILE`）<br>4. 檢查是否觸發 Telegram 風控（FloodWait）<br>5. 查看 `admin-backend/app/services/data_sources.py` 中的會話創建邏輯 |

**監控位置**：
- 後端：`/api/v1/sessions` 端點，檢查返回的會話狀態
- 主程序：`main.py` 日誌
- 會話服務：`session_service/` 日誌

### 4. 外部 AI 調用超時數

| 指標 | 說明 | 關注點 / 建議閾值 | 告警產生後的排查思路 |
|------|------|-----------------|-------------------|
| `ai_api_timeout_count` | AI API 調用超時次數（1 分鐘內） | **警告**：> 5 次<br>**嚴重**：> 20 次 | 1. 檢查 OpenAI API Key 是否有效（`OPENAI_API_KEY`）<br>2. 檢查網絡連接（防火牆、代理）<br>3. 檢查 OpenAI API 服務狀態（https://status.openai.com）<br>4. 檢查 API 限流（Rate Limit）<br>5. 查看 `main.py` 中的 AI 調用日誌<br>6. 檢查 `utils/business_ai.py` 中的超時設置 |

**監控位置**：
- 主程序：`main.py` 日誌
- 工具模塊：`utils/business_ai.py` 日誌

### 5. 系統資源使用率

| 指標 | 說明 | 關注點 / 建議閾值 | 告警產生後的排查思路 |
|------|------|-----------------|-------------------|
| `cpu_usage_percent` | CPU 使用率 | **警告**：> 80%<br>**嚴重**：> 95% | 1. 檢查是否有進程佔用過多 CPU<br>2. 檢查是否有死循環或無限遞歸<br>3. 查看 `http://localhost:3000/monitoring` 系統監控頁面<br>4. 使用 `top` 或 `htop` 查看進程詳情 |
| `memory_usage_percent` | 內存使用率 | **警告**：> 70%<br>**嚴重**：> 90% | 1. 檢查是否有內存洩漏<br>2. 檢查緩存是否過大（Redis）<br>3. 檢查數據庫連接池是否正常釋放<br>4. 查看 `http://localhost:3000/monitoring` 系統監控頁面<br>5. 使用 `free -h` 查看內存詳情 |
| `disk_usage_percent` | 磁盤使用率 | **警告**：> 80%<br>**嚴重**：> 95% | 1. 檢查日誌文件是否過大（`logs/`）<br>2. 檢查備份文件是否過多（`backup/`）<br>3. 檢查數據庫文件大小<br>4. 清理舊日誌和備份文件 |

**監控位置**：
- 後端：`/api/v1/system/monitor` 端點返回的 `metrics`
- 前端：`http://localhost:3000/monitoring` 系統監控頁面
- 系統：使用 `psutil`（後端）或系統監控工具

---

## 告警配置

### Prometheus 告警規則（示例）

**配置文件**：`admin-backend/prometheus.yml`

**告警規則文件**（建議創建 `admin-backend/alerts.yml`）：

```yaml
groups:
  - name: admin_backend_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API 錯誤率過高"
          description: "5xx 錯誤率超過 5%，持續 5 分鐘"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API 響應時間過長"
          description: "95% 分位數響應時間超過 3 秒"

      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率過高"
          description: "CPU 使用率超過 80%，持續 10 分鐘"

      - alert: HighMemoryUsage
        expr: memory_usage_percent > 70
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "內存使用率過高"
          description: "內存使用率超過 70%，持續 10 分鐘"
```

### 告警通道

根據 `docs/monitoring_and_release.md`，支持以下告警通道：

1. **Telegram Bot**：自建告警 Bot，通過 API 發送消息
2. **Slack**：Incoming Webhook
3. **Email**：使用 SES / SendGrid

**TODO：實現告警管理器**

建議創建 `admin-backend/app/services/alert_manager.py`：

```python
# 示例結構（待實現）
class AlertManager:
    def send_alert(self, level: str, message: str):
        """發送告警消息"""
        # 支持 Telegram、Slack、Email
        pass
```

---

## 問題定位指南

### 從 admin-backend 日誌定位問題

**日誌位置**：
- Docker：`docker compose logs admin-backend`
- 本地運行：終端輸出或 `logs/` 目錄

**關鍵日誌關鍵詞**：
- `ERROR`：錯誤信息
- `WARNING`：警告信息
- `Traceback`：異常堆棧
- `Database`：數據庫相關錯誤
- `Redis`：Redis 相關錯誤

**排查步驟**：
1. 查看最近的 ERROR 日誌
2. 檢查異常堆棧，定位錯誤位置
3. 檢查相關配置（環境變量、數據庫連接等）
4. 檢查外部服務連接

### 從 saas-demo 界面定位問題

**Dashboard 頁面**（`http://localhost:3000/`）：
- 檢查統計卡片是否顯示異常數據
- 檢查響應時間趨勢圖是否有異常峰值
- 檢查系統狀態卡片是否顯示錯誤

**系統監控頁面**（`http://localhost:3000/monitoring`）：
- 檢查系統健康狀態
- 檢查資源使用情況（CPU、內存、磁盤）
- 檢查服務狀態

**日誌中心頁面**（`http://localhost:3000/logs`）：
- 查看錯誤級別的日誌
- 搜索關鍵錯誤信息
- 查看日誌詳情（堆棧信息）

### 從 session_service 定位問題

**日誌位置**：
- 主程序：`main.py` 日誌輸出
- 會話服務：`session_service/` 模塊日誌

**關鍵檢查點**：
1. 會話連接狀態
2. Telegram API 調用結果
3. FloodWait 觸發次數
4. 會話創建/銷毀事件

---

## 監控儀表板

### Prometheus + Grafana

**配置**：
- Prometheus 配置：`admin-backend/prometheus.yml`
- Grafana Dashboard：**TODO：創建 Grafana Dashboard JSON**

**關鍵指標查詢**：

```promql
# API 錯誤率
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# API 響應時間（95% 分位數）
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# CPU 使用率
cpu_usage_percent

# 內存使用率
memory_usage_percent
```

### saas-demo 監控界面

**訪問地址**：`http://localhost:3000/monitoring`

**顯示內容**：
- 系統健康狀態
- 資源使用情況（CPU、內存、磁盤）
- 服務狀態
- 實時刷新（每 30 秒）

---

## 告警響應流程

### 1. 告警接收

- 告警發送到配置的通道（Telegram / Slack / Email）
- 記錄告警時間和級別

### 2. 問題排查

按照「告警產生後的排查思路」進行排查：

1. **確認告警真實性**：檢查是否為誤報
2. **定位問題根源**：查看日誌、監控數據
3. **評估影響範圍**：確認影響的服務和用戶

### 3. 問題處理

- **自動恢復**：如果是暫時性問題，等待自動恢復
- **手動修復**：根據排查結果進行修復
- **回滾**：如果問題嚴重，考慮回滾到上一個版本

### 4. 告警關閉

- 確認問題已解決
- 關閉告警
- 記錄問題原因和處理過程

---

## 監控檢查清單

### 日常檢查（每天）

- [ ] 檢查 API 錯誤率是否正常（< 1%）
- [ ] 檢查 API 響應時間是否正常（P95 < 1000ms）
- [ ] 檢查系統資源使用率（CPU < 80%, Memory < 70%）
- [ ] 檢查關鍵服務是否正常運行

### 週期檢查（每週）

- [ ] 檢查日誌文件大小，必要時清理
- [ ] 檢查備份文件，確認備份正常
- [ ] 檢查告警規則是否有效
- [ ] 檢查監控儀表板是否正常

### 發布前檢查

- [ ] 確認所有監控指標正常
- [ ] 確認告警通道正常
- [ ] 確認日誌記錄正常
- [ ] 確認備份機制正常

---

**最後更新**: 2024-12-19
