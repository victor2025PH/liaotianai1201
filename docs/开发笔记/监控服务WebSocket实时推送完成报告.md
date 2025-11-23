# 監控服務 WebSocket 實時推送完成報告

> **完成日期**: 2025-01-XX  
> **狀態**: ✅ 已完成

---

## 完成項目總覽

本次完善了監控服務 HTTP API，添加了 WebSocket 實時推送功能：

1. ✅ **WebSocket 實時指標推送** (`/ws/metrics`)
2. ✅ **WebSocket 實時告警推送** (`/ws/alerts`)
3. ✅ **連接管理器** - 管理 WebSocket 連接和廣播任務

---

## 詳細實現說明

### 1. ✅ WebSocket 連接管理器

**文件**: `admin-backend/app/api/group_ai/monitor.py`

**功能**:
- 管理所有活躍的 WebSocket 連接
- 自動啟動/停止指標廣播任務（根據連接數）
- 處理連接斷開和清理
- 支持廣播告警消息

**關鍵代碼**:
```python
class ConnectionManager:
    """WebSocket 連接管理器"""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.metrics_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket):
        """接受 WebSocket 連接"""
        # 如果這是第一個連接，啟動指標推送任務
    
    def disconnect(self, websocket: WebSocket):
        """斷開 WebSocket 連接"""
        # 如果沒有連接了，停止指標推送任務
    
    def start_metrics_broadcast(self):
        """啟動指標廣播任務"""
        # 每 5 秒推送一次系統指標和賬號指標
```

---

### 2. ✅ WebSocket 實時指標推送

**端點**: `WS /api/v1/group-ai/monitor/ws/metrics`

**功能**:
- 客戶端連接後立即發送初始指標
- 每 5 秒自動推送系統指標和賬號指標更新
- 支持心跳檢測（ping/pong）
- 自動清理斷開的連接

**推送消息格式**:
```json
{
  "type": "metrics_update",
  "timestamp": "2025-01-XX 14:30:00",
  "system_metrics": {
    "total_accounts": 10,
    "online_accounts": 8,
    "total_messages": 1000,
    "total_replies": 800,
    "total_redpackets": 50,
    "total_errors": 5,
    "average_reply_time": 1.5
  },
  "account_metrics": [
    {
      "account_id": "account_1",
      "message_count": 100,
      "reply_count": 80,
      "redpacket_count": 5,
      "error_count": 1,
      "last_activity": "2025-01-XX 14:30:00"
    }
  ]
}
```

**心跳消息**:
```json
// 客戶端發送
{"type": "ping"}

// 服務器響應
{"type": "pong", "timestamp": "2025-01-XX 14:30:00"}
```

---

### 3. ✅ WebSocket 實時告警推送

**端點**: `WS /api/v1/group-ai/monitor/ws/alerts`

**功能**:
- 客戶端連接後立即發送最近的告警（最多 10 條）
- 實時推送新觸發的告警
- 支持心跳檢測

**推送消息格式**:
```json
{
  "type": "alert",
  "timestamp": "2025-01-XX 14:30:00",
  "alert": {
    "alert_id": "error_rate_account_1_1234567890",
    "alert_type": "error",
    "account_id": "account_1",
    "message": "賬號 account_1 錯誤率過高: 55.00% (閾值: 50.00%)",
    "resolved": false
  }
}
```

---

## 使用示例

### JavaScript 客戶端示例

#### 連接指標推送

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/group-ai/monitor/ws/metrics');

ws.onopen = () => {
  console.log('WebSocket 連接已建立');
  
  // 發送心跳
  setInterval(() => {
    ws.send(JSON.stringify({ type: 'ping' }));
  }, 30000); // 每 30 秒
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'metrics_update') {
    console.log('收到指標更新:', data);
    // 更新 UI
    updateMetricsUI(data.system_metrics, data.account_metrics);
  } else if (data.type === 'pong') {
    console.log('收到心跳響應');
  }
};

ws.onerror = (error) => {
  console.error('WebSocket 錯誤:', error);
};

ws.onclose = () => {
  console.log('WebSocket 連接已關閉');
};
```

#### 連接告警推送

```javascript
const alertWs = new WebSocket('ws://localhost:8000/api/v1/group-ai/monitor/ws/alerts');

alertWs.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'alert') {
    console.log('收到新告警:', data.alert);
    // 顯示告警通知
    showAlertNotification(data.alert);
  }
};
```

### Python 客戶端示例

```python
import asyncio
import websockets
import json

async def connect_metrics():
    uri = "ws://localhost:8000/api/v1/group-ai/monitor/ws/metrics"
    async with websockets.connect(uri) as websocket:
        # 接收消息
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "metrics_update":
                print(f"收到指標更新: {data['system_metrics']}")
            elif data.get("type") == "pong":
                print("收到心跳響應")

# 運行
asyncio.run(connect_metrics())
```

---

## 性能優化

### 1. 按需啟動廣播任務

- 只有當有客戶端連接時才啟動指標廣播任務
- 當所有客戶端斷開時自動停止任務
- 節省服務器資源

### 2. 連接管理

- 自動檢測和清理斷開的連接
- 防止內存泄漏
- 支持多客戶端並發連接

### 3. 錯誤處理

- 發送失敗時自動清理連接
- 廣播任務出錯時自動重試
- 不會因為單個連接錯誤影響其他連接

---

## 修改文件清單

1. `admin-backend/app/api/group_ai/monitor.py` - 添加 WebSocket 端點和連接管理器

---

## API 端點總覽

### HTTP 端點（已存在）

| 方法 | 路徑 | 功能 |
|------|------|------|
| GET | `/api/v1/group-ai/monitor/accounts/metrics` | 獲取賬號指標 |
| GET | `/api/v1/group-ai/monitor/system` | 獲取系統指標 |
| GET | `/api/v1/group-ai/monitor/alerts` | 獲取告警列表 |
| POST | `/api/v1/group-ai/monitor/alerts/check` | 執行告警檢查 |
| POST | `/api/v1/group-ai/monitor/alerts/{alert_id}/resolve` | 解決告警 |
| GET | `/api/v1/group-ai/monitor/events` | 獲取事件日誌 |

### WebSocket 端點（新增）

| 類型 | 路徑 | 功能 |
|------|------|------|
| WS | `/api/v1/group-ai/monitor/ws/metrics` | 實時指標推送 |
| WS | `/api/v1/group-ai/monitor/ws/alerts` | 實時告警推送 |

---

## 測試建議

### 1. WebSocket 連接測試

使用瀏覽器控制台測試：

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/group-ai/monitor/ws/metrics');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### 2. 多客戶端測試

同時打開多個 WebSocket 連接，驗證：
- 所有客戶端都能收到指標更新
- 斷開一個連接不影響其他連接
- 所有連接斷開後任務自動停止

### 3. 告警推送測試

1. 連接告警 WebSocket
2. 觸發一個告警（通過 API 或實際操作）
3. 驗證告警消息是否實時推送

---

## 後續優化建議

### 短期（1週內）

- [ ] 添加訂閱特定賬號指標的功能
- [ ] 添加自定義推送頻率（客戶端可配置）
- [ ] 添加連接認證（防止未授權訪問）

### 中期（2-4週）

- [ ] 實現指標數據壓縮（減少傳輸量）
- [ ] 添加指標歷史回放功能
- [ ] 實現客戶端重連機制

### 長期（1-2個月）

- [ ] 支持多服務器部署（Redis Pub/Sub）
- [ ] 實現指標聚合和降採樣
- [ ] 添加性能監控和優化

---

## 總結

監控服務 HTTP API 已完善，現在支持：

1. **完整的 HTTP API**: 獲取指標、告警、事件日誌等
2. **WebSocket 實時推送**: 指標和告警的實時推送
3. **智能連接管理**: 按需啟動/停止廣播任務
4. **錯誤處理**: 完善的錯誤處理和連接清理

系統現在具備完整的監控 API 能力，支持 HTTP 輪詢和 WebSocket 實時推送兩種方式。

---

**狀態**: ✅ 監控服務 HTTP API 完善完成，WebSocket 實時推送功能已實現

