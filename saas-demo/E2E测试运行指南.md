# E2E 測試運行指南

> **更新日期**: 2025-01-28  
> **狀態**: 準備運行

---

## 📋 測試文件列表

當前共有 **10 個 E2E 測試文件**：

1. `e2e/example.spec.ts` - 示例測試（基礎頁面測試）
2. `e2e/dashboard.spec.ts` - Dashboard 頁面測試
3. `e2e/navigation.spec.ts` - 導航測試
4. `e2e/pages.spec.ts` - 頁面渲染測試
5. `e2e/accounts-management.spec.ts` - 賬號管理測試
6. `e2e/api-interaction.spec.ts` - API 交互測試
7. `e2e/data-sync.spec.ts` - 數據同步測試
8. `e2e/group-ai.spec.ts` - Group AI 功能測試
9. `e2e/monitor-dashboard.spec.ts` - 監控儀表板測試
10. `e2e/websocket.spec.ts` - WebSocket 測試

---

## 🚀 運行測試步驟

### 前置要求

1. **安裝依賴**（如未安裝）：
   ```bash
   cd saas-demo
   npm install
   ```

2. **安裝 Playwright 瀏覽器**（如未安裝）：
   ```bash
   npx playwright install chromium
   # 或安裝所有瀏覽器
   npx playwright install
   ```

3. **確保後端服務運行**（可選，如果測試需要後端 API）：
   ```bash
   cd admin-backend
   poetry run uvicorn app.main:app --reload
   ```

### 方法 1: 運行所有測試

```bash
cd saas-demo
npm run test:e2e
```

這將：
- 自動啟動開發服務器（如果未運行）
- 運行所有 E2E 測試
- 生成 HTML 測試報告

### 方法 2: 運行特定測試文件

```bash
# 運行示例測試
npx playwright test e2e/example.spec.ts

# 運行 Dashboard 測試
npx playwright test e2e/dashboard.spec.ts

# 運行導航測試
npx playwright test e2e/navigation.spec.ts
```

### 方法 3: 使用 UI 模式（推薦用於調試）

```bash
cd saas-demo
npm run test:e2e:ui
```

這將打開 Playwright 的交互式 UI，方便：
- 查看測試執行過程
- 調試失敗的測試
- 查看頁面截圖和視頻

### 方法 4: 使用有頭模式運行

```bash
cd saas-demo
npm run test:e2e:headed
```

這將在可見的瀏覽器窗口中運行測試，方便觀察測試過程。

---

## ⚙️ 配置說明

### Playwright 配置

配置文件：`playwright.config.ts`

**關鍵配置**：
- **基礎 URL**: `http://localhost:3001`（與 dev 服務器端口一致）
- **超時時間**: 30 秒
- **重試次數**: CI 環境 2 次，本地 0 次
- **並行執行**: 啟用
- **自動啟動服務器**: 是（如果未運行）

### 端口配置

- **開發服務器端口**: 3001（在 `package.json` 中設置）
- **Playwright 基礎 URL**: 3001（已在配置中修復）

---

## 📊 測試結果

### 查看測試報告

運行測試後，會在 `playwright-report/` 目錄生成 HTML 報告：

```bash
# 打開 HTML 報告
npx playwright show-report
```

報告包含：
- 測試通過/失敗統計
- 失敗測試的詳細錯誤信息
- 截圖和視頻（如果測試失敗）
- 測試執行時間

### 查看測試列表

```bash
# 列出所有測試（不運行）
npx playwright test --list
```

---

## 🔧 常見問題

### 1. 端口衝突

**問題**: 端口 3001 已被占用

**解決方案**:
```bash
# 檢查端口使用情況
netstat -ano | findstr :3001

# 或更改端口
# 修改 package.json 中的 dev 腳本端口
# 修改 playwright.config.ts 中的 baseURL
```

### 2. Playwright 瀏覽器未安裝

**問題**: 錯誤提示瀏覽器未找到

**解決方案**:
```bash
npx playwright install chromium
# 或安裝所有瀏覽器
npx playwright install
```

### 3. 測試超時

**問題**: 測試在 30 秒內未完成

**解決方案**:
- 檢查網絡連接
- 確認後端服務正常運行
- 增加超時時間（在測試中或配置中）

### 4. 開發服務器啟動失敗

**問題**: Playwright 無法啟動開發服務器

**解決方案**:
- 手動啟動開發服務器：`npm run dev`
- 確保 `package.json` 中的 dev 腳本正確
- 檢查依賴是否已安裝

---

## 📝 測試調試技巧

### 1. 使用 Playwright Inspector

```bash
# 使用調試模式運行
PWDEBUG=1 npx playwright test e2e/example.spec.ts
```

### 2. 添加調試斷點

在測試中添加：
```typescript
await page.pause(); // 暫停測試，打開調試工具
```

### 3. 查看控制台輸出

```typescript
page.on('console', msg => console.log('Browser console:', msg.text()));
```

### 4. 查看網絡請求

```typescript
page.on('request', request => console.log('Request:', request.url()));
page.on('response', response => console.log('Response:', response.url(), response.status()));
```

---

## ✅ 測試檢查清單

運行測試前，請確認：

- [ ] Node.js 和 npm 已安裝
- [ ] 項目依賴已安裝 (`npm install`)
- [ ] Playwright 瀏覽器已安裝 (`npx playwright install`)
- [ ] 開發服務器可以正常啟動 (`npm run dev`)
- [ ] 端口 3001 未被占用
- [ ] 後端 API 服務運行正常（如需要）

---

## 📈 下一步

1. **運行所有測試**：
   ```bash
   cd saas-demo
   npm run test:e2e
   ```

2. **查看測試報告**：
   ```bash
   npx playwright show-report
   ```

3. **修復失敗的測試**：
   - 查看錯誤信息
   - 使用 UI 模式調試
   - 修復代碼或測試

4. **更新測試文檔**：
   - 記錄測試結果
   - 更新測試狀態

---

## 🔗 相關文檔

- [Playwright 官方文檔](https://playwright.dev/)
- [Next.js 測試指南](https://nextjs.org/docs/testing)
- 項目測試文檔：`docs/开发笔记/下一步工作执行计划_20250128.md`

---

**狀態**: 🟢 準備運行  
**最後更新**: 2025-01-28
