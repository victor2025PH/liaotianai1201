# 聊天 AI 控制台

企業級聊天 AI 系統管理後台，基於 Next.js + Tailwind CSS + shadcn/ui 構建。

## 技術棧

- **前端框架**: Next.js 16.0.2 (App Router)
- **樣式**: Tailwind CSS
- **UI 組件**: shadcn/ui
- **狀態管理**: React Hooks
- **API 客戶端**: 統一封裝，支持自動 fallback 到 mock 數據
- **類型安全**: TypeScript

## 快速開始

### 安裝依賴

```bash
npm install
```

### 啟動開發服務器

```bash
npm run dev
```

訪問 http://localhost:3000

### 構建生產版本

```bash
npm run build
npm start
```

## 頁面路徑與功能

### 前端頁面（http://localhost:3000）

| 路徑 | 功能 | 主要特性 | 狀態 |
|------|------|---------|------|
| `/` | 總覽儀表板 | 統計卡片、響應時間趨勢圖、最近會話列表、錯誤列表、系統狀態 | ✅ |
| `/sessions` | 會話列表 | 分頁、搜索（session_id/用戶）、時間範圍篩選、狀態篩選、會話詳情 Dialog | ✅ |
| `/sessions/[id]` | 會話詳情 | 會話信息、消息記錄、元數據 | ✅ |
| `/logs` | 日誌中心 | 分頁、級別過濾（error/warning/info）、關鍵詞搜索、日誌詳情 Dialog | ✅ |
| `/settings/alerts` | 告警配置 | 告警閾值設置、通知方式配置、告警規則列表、啟用/禁用規則 | ✅ |
| `/monitoring` | 系統監控 | 系統健康狀態、資源使用情況（CPU/內存/磁盤）、服務狀態、實時刷新（30s） | ✅ |

## 後端 API（http://localhost:8000）

### 基礎路徑

所有 API 路徑前綴：`/api/v1`

### API 接口列表

#### Dashboard
| 路徑 | 方法 | 功能 | 參數 | 返回類型 |
|------|------|------|------|---------|
| `/dashboard` | GET | Dashboard 統計數據 | - | `DashboardData` |
| `/metrics` | GET | 響應時間和系統狀態指標 | - | `MetricsData` |

#### Sessions（會話）
| 路徑 | 方法 | 功能 | 參數 | 返回類型 |
|------|------|------|------|---------|
| `/sessions` | GET | 會話列表 | `page`, `page_size`, `q`（搜索）, `range`（24h/7d）, `start_date`, `end_date` | `SessionList` |
| `/sessions/{id}` | GET | 會話詳情 | `id`（路徑參數） | `SessionDetail` |

#### Logs（日誌）
| 路徑 | 方法 | 功能 | 參數 | 返回類型 |
|------|------|------|------|---------|
| `/logs` | GET | 日誌列表 | `page`, `page_size`, `level`（error/warning/info）, `q`（搜索） | `LogList` |

#### Settings（設置）
| 路徑 | 方法 | 功能 | 參數 | 返回類型 |
|------|------|------|------|---------|
| `/settings/alerts` | GET | 獲取告警設置 | - | `AlertSettings` |
| `/settings/alerts` | POST | 保存告警設置 | Body: `AlertSettings` | `{ success, message }` |
| `/settings/alerts/rules` | GET | 獲取告警規則列表 | - | `AlertRuleList`（待實現） |
| `/settings/alerts/rules/{id}` | PUT | 更新告警規則 | `id`（路徑參數）, Body: `Partial<AlertRule>` | `AlertRule`（待實現） |

#### System Monitor（系統監控）
| 路徑 | 方法 | 功能 | 參數 | 返回類型 |
|------|------|------|------|---------|
| `/system/monitor` | GET | 系統監控數據 | - | `SystemMonitorData` |

### 請求示例

```bash
# 獲取會話列表
curl http://localhost:8000/api/v1/sessions?page=1&page_size=20

# 獲取日誌列表（過濾錯誤級別）
curl http://localhost:8000/api/v1/logs?level=error&page=1&page_size=20

# 獲取會話詳情
curl http://localhost:8000/api/v1/sessions/session-001
```

## Mock 數據 Fallback

### 自動啟用條件

當後端 API 不可用時，系統會自動切換到 mock 數據模式。觸發條件包括：

1. **網絡錯誤**：無法連接到後端服務器（`Failed to fetch`、`NetworkError`）
2. **超時**：API 請求超過 5 秒未響應（`AbortError`）
3. **5xx 錯誤**：服務器內部錯誤（500-599）→ 返回帶 `error` 字段的結果，同時嘗試使用 mock 數據
4. **404 錯誤**：接口不存在 → 使用 mock 數據（如果可用）

### 不觸發 Mock Fallback 的情況

- **4xx 錯誤（除 404）**：參數錯誤等客戶端錯誤 → 僅顯示 toast 提示，不使用 mock 數據

### Mock 數據位置

Mock 數據定義在以下文件中：
- `src/mock/sessions.ts` - 會話列表和詳情
- `src/mock/logs.ts` - 日誌記錄
- `src/mock/stats.ts` - 系統監控數據
- `src/lib/api-client.ts` - Dashboard 和 Metrics 的 mock 數據

### 視覺提示

當使用 mock 數據時，頁面會顯示：
- **黃色 Alert 提示條**：顯示「當前展示的是模擬數據。後端服務器不可用，已自動切換到模擬數據模式。」
- **描述文字標記**：部分組件會在描述中顯示「(模擬數據)」標記

### 如何禁用 Mock Fallback

如果需要強制使用真實 API（禁用 mock fallback），可以修改 `src/lib/api-client.ts`：

```typescript
// 在 apiClient 函數的 catch 塊中，註釋掉 mock 數據返回邏輯
// const mockData = getMockData<T>(endpoint);
// return { ok: true, data: mockData, _isMock: true };
// 改為直接返回錯誤：
return {
  ok: false,
  error: {
    message: errorMessage,
    code: "NETWORK_ERROR",
  },
};
```

### 如何啟用 Mock Fallback

Mock fallback 默認已啟用，無需額外配置。如果後端服務器運行正常，系統會優先使用真實 API 數據。

### Mock 數據結構

所有 mock 數據都遵循與真實 API 相同的數據結構，確保前端組件可以無縫切換：

- **Dashboard**: `src/lib/api-client.ts` 中的 `mockData.dashboard`
- **Metrics**: `src/lib/api-client.ts` 中的 `mockData.metrics`
- **Sessions**: `src/mock/sessions.ts` → `mockSessions`, `mockSessionDetail`
- **Logs**: `src/mock/logs.ts` → `mockLogs`
- **System Monitor**: `src/mock/stats.ts` → `mockSystemStats`
- **Alert Rules**: `src/lib/api.ts` 中的 `getAlertRules()` 函數內聯 mock 數據

## 系統監控數據防禦式處理

### 數據結構驗證

所有使用系統監控數據的組件都實現了防禦式邏輯，確保在數據不完整或缺失時不會崩潰：

1. **數組操作前檢查**：
   ```typescript
   const statusItems = Array.isArray(data?.system_status?.status_items) 
     ? data.system_status.status_items 
     : [];
   ```

2. **對象字段默認值**：
   ```typescript
   const health = data.health || {
     status: "unknown",
     uptime_seconds: 0,
     version: "unknown",
     timestamp: new Date().toISOString(),
   };
   ```

3. **空數據友好提示**：
   - 當 `status_items` 為空時，顯示「暫時無法獲取系統狀態數據，請稍後重試」
   - 當 `services` 為空時，顯示「暫無服務狀態數據」

### 錯誤邊界（Error Boundary）

Dashboard 頁面中的關鍵組件（`ResponseTimeChart`、`SystemStatus`）都包裹在 `ErrorBoundary` 中：

- 單個組件出錯不會導致整個頁面白屏
- 顯示友好的錯誤提示和重試按鈕
- 其他組件仍可正常使用

### 系統監控接口數據結構

#### `/api/v1/metrics` 返回結構

```typescript
{
  response_time: {
    data_points: Array<{ timestamp: string; value: number }>;
    average: number;
    min: number;
    max: number;
    trend: string;
  };
  system_status: {
    status_items: Array<{
      label: string;
      status: string;
      value: string;
      description: string;
    }>;
    last_updated: string;
  };
}
```

#### `/api/v1/system/monitor` 返回結構

```typescript
{
  health: {
    status: string;        // "healthy" | "degraded" | "unhealthy"
    uptime_seconds: number;
    version: string;
    timestamp: string;
  };
  metrics: {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    disk_usage_percent: number;
    active_connections: number;
    queue_length: number;
    timestamp: string;
  };
  services: Record<string, {
    status: string;
    uptime?: number;
    response_time_ms?: number;
    active_sessions?: number;
  }>;
}
```

### 錯誤處理策略

1. **網絡錯誤/超時**：
   - 自動切換到 mock 數據
   - 顯示黃色 Alert 提示條

2. **5xx 服務器錯誤**：
   - 返回帶 `error` 字段的結果
   - 嘗試使用 mock 數據作為 fallback

3. **數據結構不完整**：
   - 使用默認值填充缺失字段
   - 顯示空狀態提示（而非錯誤）

4. **組件渲染錯誤**：
   - ErrorBoundary 捕獲錯誤
   - 顯示友好的錯誤提示和重試按鈕
   - 不影響其他組件

## 功能特性

### ✅ 已實現

1. **統一 API 客戶端**
   - 5 秒超時自動 fallback
   - 統一的錯誤處理和 toast 提示
   - 支持 GET、POST、PUT、DELETE
   - 網絡錯誤/5xx 返回帶 `error` 字段的結果
   - 4xx 錯誤用 toast 提示（參數錯誤等）

2. **實時數據更新**
   - Dashboard 圖表每 10 秒自動刷新
   - 系統監控每 30 秒自動刷新

3. **會話管理**
   - 會話列表（分頁、搜索、時間範圍篩選、狀態篩選）
   - 會話詳情 Dialog（消息記錄、元數據）

4. **日誌中心**
   - 日誌列表（分頁、級別篩選、關鍵詞搜索）
   - 日誌詳情 Dialog（完整 payload、堆棧信息）

5. **告警配置**
   - 讀取和保存告警設置
   - 表單驗證和 toast 提示

6. **系統監控**
   - 系統健康狀態
   - 資源使用情況（CPU、內存、磁盤）
   - 服務狀態監控

### 🚧 待實現

- [ ] 告警配置完整 CRUD（列表、創建、編輯、刪除）
- [ ] 系統監控圖表優化（CPU/內存/磁盤折線圖）
- [ ] QPS 和平均響應時間實時顯示
- [ ] 用戶認證和授權
- [ ] 會話詳情頁面（獨立路由）

## 開發指南

### 項目結構

```
saas-demo/
├── src/
│   ├── app/              # Next.js App Router 頁面
│   │   ├── page.tsx      # Dashboard
│   │   ├── sessions/     # 會話列表和詳情
│   │   ├── logs/         # 日誌中心
│   │   ├── settings/     # 設置頁面
│   │   └── monitoring/   # 系統監控
│   ├── components/       # React 組件
│   │   ├── ui/          # shadcn/ui 組件
│   │   └── dashboard/   # Dashboard 專用組件
│   ├── lib/             # 工具函數和 API 封裝
│   │   ├── api.ts       # API 函數定義
│   │   └── api-client.ts # 統一 API 客戶端
│   ├── hooks/           # React Hooks
│   └── mock/            # Mock 數據
├── public/              # 靜態資源
└── package.json
```

### 添加新 API

1. 在 `src/lib/api.ts` 中定義接口類型
2. 在 `src/lib/api.ts` 中添加 API 函數（使用 `apiGet`、`apiPost` 等）
3. 在 `src/lib/api-client.ts` 的 `mockData` 中添加對應的 mock 數據
4. 在 `src/mock/` 中創建對應的 mock 數據文件（可選）

### 添加新頁面

1. 在 `src/app/` 下創建新的路由目錄
2. 使用統一的 Layout（已在 `layout.tsx` 中配置）
3. 使用 shadcn/ui 組件保持風格一致
4. 添加加載狀態、錯誤處理和 mock 數據提示

## 環境變量

創建 `.env.local` 文件（可選）：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

默認值：`http://localhost:8000/api/v1`

## 故障排除

### 後端不可用

- 系統會自動切換到 mock 數據
- 頁面頂部會顯示提示信息
- 所有功能仍可正常使用（使用模擬數據）

### 構建錯誤

```bash
# 清理構建緩存
rm -rf .next
npm run build
```

### 類型錯誤

```bash
# 檢查 TypeScript 類型
npx tsc --noEmit
```

## 許可證

MIT
