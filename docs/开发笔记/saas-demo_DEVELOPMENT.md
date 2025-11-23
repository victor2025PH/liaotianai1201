# 聊天 AI 控制台 - 開發文檔

## 項目概述

這是一個基於 Next.js + Tailwind CSS + shadcn/ui 構建的企業級聊天 AI 後台管理系統前端應用。

- **前端端口**: `http://localhost:3000`
- **後端 API**: `http://localhost:8000/api/v1`

## 已實現的頁面

### 1. 總覽儀表板 (`/`)
- **功能**: 展示系統統計數據、響應時間趨勢圖、系統狀態卡片
- **數據來源**: 
  - `GET /api/v1/dashboard` - Dashboard 統計數據（真實 API）
  - `GET /api/v1/metrics` - 響應時間和系統狀態指標（真實 API）

### 2. 會話列表 (`/sessions`)
- **功能**: 會話列表展示、搜索、時間範圍篩選、分頁
- **數據來源**: 
  - `GET /api/v1/sessions` - 會話列表（支持 `q`, `range`, `start_date`, `end_date` 參數）（真實 API）
  - `GET /api/v1/sessions/{id}` - 會話詳情（真實 API）

### 3. 日誌中心 (`/logs`)
- **功能**: 
  - 日誌列表展示（時間、級別、類型、嚴重性、訊息、來源）
  - 級別篩選（error/warning/info）
  - 關鍵詞搜索
  - 分頁
  - 日誌詳情彈窗（點擊日誌行或操作按鈕查看完整信息）
- **數據來源**: 
  - `GET /api/v1/logs` - 日誌列表（支持 `page`, `page_size`, `level`, `q` 參數）（真實 API）

### 4. 告警設置 (`/settings/alerts`)
- **功能**: 
  - 告警閾值配置（錯誤率、最大響應時間）
  - 通知方式配置（Email、Webhook）
  - 保存/加載配置
  - Toast 提示（成功/失敗）
- **數據來源**: 
  - `GET /api/v1/settings/alerts` - 獲取告警設置（真實 API）
  - `POST /api/v1/settings/alerts` - 保存告警設置（真實 API）

### 5. 系統監控 (`/monitoring`)
- **功能**: 
  - 系統健康狀態（狀態、運行時間、版本）
  - 資源使用情況（CPU、內存、磁盤使用率、活躍連接數、隊列長度）
  - 服務狀態（API 服務器、數據庫、Redis、會話服務）
  - 自動刷新（每 30 秒）
- **數據來源**: 
  - `GET /api/v1/system/monitor` - 系統監控數據（真實 API，嘗試使用 psutil 獲取真實系統指標，不可用時回退到 mock）

## 後端 API 接口列表

| 路徑 | 方法 | 功能 | 狀態 |
|------|------|------|------|
| `/api/v1/dashboard` | GET | Dashboard 統計數據 | ✅ 真實 API |
| `/api/v1/metrics` | GET | 響應時間和系統狀態指標 | ✅ 真實 API |
| `/api/v1/sessions` | GET | 會話列表（支持搜索、時間範圍、分頁） | ✅ 真實 API |
| `/api/v1/sessions/{id}` | GET | 會話詳情 | ✅ 真實 API |
| `/api/v1/logs` | GET | 日誌列表（支持級別、搜索、分頁） | ✅ 真實 API |
| `/api/v1/settings/alerts` | GET | 獲取告警設置 | ✅ 真實 API |
| `/api/v1/settings/alerts` | POST | 保存告警設置 | ✅ 真實 API |
| `/api/v1/system/monitor` | GET | 系統監控數據 | ✅ 真實 API（部分 mock） |

## 數據來源說明

### 真實 API 數據
- ✅ Dashboard 統計數據（會話總數、錯誤數、平均響應時間等）
- ✅ 響應時間趨勢數據
- ✅ 系統狀態指標
- ✅ 會話列表和詳情
- ✅ 日誌列表
- ✅ 告警設置（讀取和保存）

### Mock 數據（後端提供）
- ⚠️ 系統監控數據：當 `psutil` 不可用時，使用 mock 數據（CPU: 45.2%, 內存: 62.5%, 磁盤: 38.1%）
- ⚠️ 部分日誌數據：後端可能返回模擬的日誌數據

## 技術棧

- **框架**: Next.js 16.0.2 (App Router)
- **樣式**: Tailwind CSS
- **UI 組件**: shadcn/ui
- **狀態管理**: React Hooks (useState, useEffect, useCallback)
- **API 客戶端**: Fetch API
- **類型安全**: TypeScript

## 開發命令

```bash
# 安裝依賴
npm install

# 啟動開發服務器
npm run dev

# 構建生產版本
npm run build

# 啟動生產服務器
npm start
```

## 側邊欄菜單

- 總覽 (`/`) - Dashboard
- 會話列表 (`/sessions`) - Sessions
- 日誌 (`/logs`) - Logs
- 告警設置 (`/settings/alerts`) - Alert Settings
- 系統監控 (`/monitoring`) - System Monitor
- 模型配置 (`/models`) - Models (待實現)
- 實驗功能 (`/experiments`) - Experiments (待實現)

## 注意事項

1. **認證**: 目前後端 API 已暫時移除認證依賴，便於開發測試
2. **錯誤處理**: 所有頁面都實現了加載骨架屏、錯誤提示和重試按鈕
3. **URL 同步**: Sessions 和 Logs 頁面的篩選條件會同步到 URL 查詢參數
4. **自動刷新**: 
   - Dashboard 響應時間圖表和系統狀態：每 10 秒自動刷新
   - 系統監控頁面：每 30 秒自動刷新
5. **Mock 數據 Fallback**: 當後端 API 5 秒內無響應時，自動切換到 mock 數據，並顯示友好提示

## 最新功能（2024-11-13）

### ✨ 統一 API 客戶端
- **文件**: `src/lib/api-client.ts`
- **功能**:
  - 5 秒超時自動 fallback 到 mock 數據
  - 統一的錯誤處理和 toast 提示
  - 支持 GET、POST、PUT、DELETE 方法
  - 自動處理網絡錯誤和超時

### ✨ 實時數據更新
- **Hooks**:
  - `useRealtimeMetrics`: 輪詢方式實時更新指標（每 5-10 秒）
  - `useSSE`: Server-Sent Events 支持（為未來擴展準備）
- **應用**:
  - Dashboard 響應時間圖表：每 10 秒自動更新
  - Dashboard 系統狀態卡片：每 10 秒自動更新
  - 系統監控頁面：每 30 秒自動更新

### ✨ 圖表優化
- 響應時間圖表添加手動刷新按鈕
- 顯示自動更新狀態
- 優化視覺效果和交互體驗

## 待實現功能

- [ ] 模型配置頁面 (`/models`)
- [ ] 實驗功能頁面 (`/experiments`)
- [ ] 用戶認證和授權
- [ ] 會話詳情頁面的完整實現
- [ ] 日誌導出功能
- [ ] 告警歷史記錄

