# 聊天 AI 控制台 - 快速啟動指南

## 📋 功能說明

### 已實現的核心功能

#### 1. **總覽儀表板** (`/`)
- ✅ 6 個統計卡片（會話量、成功率、Token 用量、錯誤數、響應時間、活躍用戶）
- ✅ 響應時間趨勢圖（每 10 秒自動刷新）
- ✅ 系統狀態監控
- ✅ 最近 10 條會話列表（點擊查看詳情）
- ✅ 最近錯誤與警告列表
- ✅ 統計卡片可點擊跳轉到對應頁面

#### 2. **會話列表** (`/sessions`)
- ✅ 分頁顯示（每頁 20 條）
- ✅ 關鍵詞搜索（session_id、用戶）
- ✅ 時間範圍篩選（全部/24 小時/7 天）
- ✅ 狀態篩選（全部/已完成/進行中/失敗）
- ✅ 會話詳情 Dialog（消息記錄、元數據）
- ✅ URL 查詢參數同步（支持書籤和分享）

#### 3. **日誌中心** (`/logs`)
- ✅ 分頁顯示（每頁 20 條）
- ✅ 級別過濾（error/warning/info）
- ✅ 關鍵詞搜索（message、logger）
- ✅ 日誌詳情 Dialog（完整 payload、堆棧信息、請求 ID）
- ✅ URL 查詢參數同步

#### 4. **告警配置** (`/settings/alerts`)
- ✅ 告警閾值設置（錯誤率、最大響應時間）
- ✅ 通知方式配置（郵件/Webhook）
- ✅ 告警規則列表（表格展示）
- ✅ 規則啟用/禁用切換（前端 state + mock 數據）
- ✅ 設置保存和加載（對接後端 API）

#### 5. **系統監控** (`/monitoring`)
- ✅ 系統健康狀態（狀態、運行時間、版本）
- ✅ 資源使用情況（CPU、內存、磁盤使用率）
- ✅ 服務狀態監控
- ✅ 實時刷新（每 30 秒自動更新）

### 技術特性

- ✅ **統一 API 封裝**：所有請求通過 `src/lib/api.ts` 和 `src/lib/api-client.ts`
- ✅ **類型安全**：完整的 TypeScript 類型定義
- ✅ **防禦式編程**：避免 `undefined`、`slice` 等運行時錯誤
- ✅ **Mock Fallback**：後端不可用時自動切換到 mock 數據
- ✅ **友好錯誤提示**：4xx 用 toast，5xx/網絡錯誤顯示頁面提示
- ✅ **實時更新**：Dashboard 和監控頁面支持自動刷新
- ✅ **響應式設計**：適配桌面和移動端

## 🚀 如何啟動

### 前置條件

- Node.js 18+ 
- npm 或 yarn
- （可選）後端服務運行在 `http://localhost:8000`

### 啟動步驟

1. **安裝依賴**
   ```bash
   cd saas-demo
   npm install
   ```

2. **啟動開發服務器**
   ```bash
   npm run dev
   ```

3. **訪問應用**
   - 打開瀏覽器訪問：http://localhost:3000
   - 如果後端未運行，系統會自動使用 mock 數據

### 環境變量（可選）

創建 `.env.local` 文件：
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### 構建生產版本

```bash
npm run build
npm start
```

## 📍 頁面訪問地址

| 頁面 | URL | 說明 |
|------|-----|------|
| 總覽儀表板 | http://localhost:3000/ | 系統總覽和關鍵指標 |
| 會話列表 | http://localhost:3000/sessions | 查看和管理會話記錄 |
| 會話詳情 | http://localhost:3000/sessions/[id] | 單個會話的詳細信息 |
| 日誌中心 | http://localhost:3000/logs | 系統日誌和錯誤記錄 |
| 告警配置 | http://localhost:3000/settings/alerts | 配置告警規則和通知 |
| 系統監控 | http://localhost:3000/monitoring | 實時系統監控數據 |

## 🔌 後端 API 對接

### 後端地址
- 默認：`http://localhost:8000/api/v1`
- 可通過環境變量 `NEXT_PUBLIC_API_BASE_URL` 配置

### 主要 API 端點

- `GET /api/v1/dashboard` - Dashboard 統計數據
- `GET /api/v1/metrics` - 響應時間和系統狀態指標
- `GET /api/v1/sessions` - 會話列表（支持分頁、搜索、篩選）
- `GET /api/v1/sessions/{id}` - 會話詳情
- `GET /api/v1/logs` - 日誌列表（支持分頁、級別過濾、搜索）
- `GET /api/v1/settings/alerts` - 獲取告警設置
- `POST /api/v1/settings/alerts` - 保存告警設置
- `GET /api/v1/system/monitor` - 系統監控數據

### Mock Fallback 觸發條件

當以下情況發生時，系統會自動切換到 mock 數據：

1. **網絡錯誤**：無法連接到後端（`Failed to fetch`）
2. **超時**：請求超過 5 秒未響應
3. **5xx 錯誤**：服務器內部錯誤（500-599）
4. **404 錯誤**：接口不存在

**注意**：4xx 錯誤（除 404）不會觸發 mock fallback，僅顯示 toast 提示。

## 🛠️ 開發建議

### 添加新頁面

1. 在 `src/app/` 下創建路由目錄
2. 使用統一的 Layout 和 shadcn/ui 組件
3. 通過 `src/lib/api.ts` 調用 API
4. 處理 loading、error、空數據狀態
5. 添加 mock 數據 fallback 和視覺提示

### 添加新 API

1. 在 `src/lib/api.ts` 中定義 TypeScript 類型
2. 添加 API 函數（使用 `apiGet`、`apiPost` 等）
3. 在 `src/lib/api-client.ts` 的 `mockData` 中添加 mock 數據
4. 創建對應的 hook（如 `useXXX.ts`）

### 調試技巧

- 打開瀏覽器開發者工具查看 Network 請求
- 檢查 Console 中的錯誤和警告
- 查看 `src/lib/api-client.ts` 中的 mock 數據切換邏輯
- 使用 `npm run build` 檢查 TypeScript 類型錯誤

## 📝 注意事項

1. **後端未運行時**：系統會自動使用 mock 數據，頁面會顯示黃色提示條
2. **類型安全**：所有 API 調用都有完整的 TypeScript 類型定義
3. **防禦式邏輯**：所有數據訪問都經過 null/undefined 檢查
4. **錯誤處理**：4xx 錯誤用 toast 提示，5xx/網絡錯誤顯示頁面提示和重試按鈕

## 🎯 下一步開發建議

- [ ] 告警規則完整 CRUD（創建、編輯、刪除）
- [ ] 系統監控圖表優化（CPU/內存/磁盤折線圖）
- [ ] QPS 和平均響應時間實時顯示
- [ ] 用戶認證和授權
- [ ] 會話詳情獨立頁面（替代 Dialog）

---

**最後更新**：2024-12-19
**項目狀態**：✅ 核心功能已完成，可正常使用

