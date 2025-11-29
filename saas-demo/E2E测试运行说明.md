# E2E 測試運行說明

> **日期**: 2025-01-28  
> **狀態**: ✅ 準備完成

---

## 🚀 快速運行測試

### 方式 1：使用 npm 腳本（最簡單）

在 `saas-demo` 目錄下執行：

```bash
npm run test:e2e
```

### 方式 2：使用 Playwright 命令

```bash
npx playwright test
```

### 方式 3：使用批處理文件（Windows）

```bash
run-tests.bat
```

### 方式 4：使用 Node.js 腳本

```bash
node run-test-quick.js
```

---

## 📋 測試文件清單

當前共有 **10 個 E2E 測試文件**：

1. ✅ `e2e/example.spec.ts` - 基礎示例測試
2. ✅ `e2e/dashboard.spec.ts` - Dashboard 頁面測試
3. ✅ `e2e/navigation.spec.ts` - 導航功能測試
4. ✅ `e2e/pages.spec.ts` - 頁面渲染測試
5. ✅ `e2e/accounts-management.spec.ts` - 賬號管理測試
6. ✅ `e2e/api-interaction.spec.ts` - API 交互測試
7. ✅ `e2e/data-sync.spec.ts` - 數據同步測試
8. ✅ `e2e/group-ai.spec.ts` - Group AI 功能測試
9. ✅ `e2e/monitor-dashboard.spec.ts` - 監控儀表板測試
10. ✅ `e2e/websocket.spec.ts` - WebSocket 連接測試

---

## ⚙️ 已完成的準備工作

### 1. ✅ 修復端口配置
- 統一使用端口 3001
- 更新了 `playwright.config.ts`

### 2. ✅ 創建運行腳本
- `run-e2e-tests.ps1` - PowerShell 腳本
- `run-e2e-tests-simple.ps1` - 簡化 PowerShell 腳本
- `run-tests.bat` - Windows 批處理文件
- `run-test-quick.js` - Node.js 腳本
- `check-test-env.js` - 環境檢查腳本

### 3. ✅ 配置說明
- 自動啟動開發服務器
- 超時時間：30 秒
- 失敗重試：CI 環境 2 次
- 生成 HTML 報告

---

## 🔍 測試執行步驟

### 步驟 1：檢查環境

```bash
node check-test-env.js
```

這將檢查：
- package.json 是否存在
- 依賴是否安裝
- 測試文件是否存在
- Playwright 配置是否正確

### 步驟 2：安裝 Playwright 瀏覽器（如需要）

如果首次運行，可能需要安裝瀏覽器：

```bash
npx playwright install chromium
```

或安裝所有瀏覽器：

```bash
npx playwright install
```

### 步驟 3：運行測試

選擇任一方式運行：

```bash
# 方式 1：npm 腳本
npm run test:e2e

# 方式 2：直接運行
npx playwright test

# 方式 3：運行單個測試文件
npx playwright test e2e/example.spec.ts

# 方式 4：使用 UI 模式（推薦用於調試）
npm run test:e2e:ui
```

### 步驟 4：查看結果

#### 查看 HTML 報告

```bash
npx playwright show-report
```

報告包含：
- 測試通過/失敗統計
- 詳細的錯誤信息
- 失敗測試的截圖和視頻
- 測試執行時間

#### 查看命令行輸出

測試運行時會在終端顯示實時結果。

---

## 📊 預期測試內容

### 基礎測試 (example.spec.ts)
- 首頁顯示
- 導航元素存在

### Dashboard 測試 (dashboard.spec.ts)
- Dashboard 標題顯示
- 統計卡片顯示
- 最近會話列表
- 刷新功能

### 導航測試 (navigation.spec.ts)
- 導航到 Dashboard
- 導航到會話列表
- 導航到日誌頁面
- 導航到賬號管理

### 頁面渲染測試 (pages.spec.ts)
- Dashboard 頁面加載
- 會話列表頁面加載
- 日誌頁面加載
- Group AI 頁面加載
- 監控頁面加載

### 其他功能測試
- 賬號管理 CRUD 操作
- API 交互驗證
- 數據同步功能
- WebSocket 連接

---

## ⚠️ 常見問題

### 1. 端口衝突

**問題**: 端口 3001 已被占用

**解決**:
```bash
# 檢查端口
netstat -ano | findstr :3001

# 或更改端口（需要同時修改 package.json 和 playwright.config.ts）
```

### 2. Playwright 瀏覽器未安裝

**問題**: 錯誤提示找不到瀏覽器

**解決**:
```bash
npx playwright install chromium
```

### 3. 依賴未安裝

**問題**: 找不到 @playwright/test 模塊

**解決**:
```bash
npm install
```

### 4. 測試超時

**問題**: 測試在 30 秒內未完成

**解決**:
- 檢查開發服務器是否正常運行
- 檢查網絡連接
- 增加超時時間（在測試文件中）

### 5. 開發服務器無法啟動

**問題**: Playwright 無法自動啟動服務器

**解決**:
- 手動啟動服務器：`npm run dev`
- 確保 package.json 中的 dev 腳本正確
- 檢查是否有語法錯誤

---

## 🐛 調試技巧

### 1. 使用 UI 模式

```bash
npm run test:e2e:ui
```

這會打開 Playwright 的交互式界面，可以：
- 逐步執行測試
- 查看頁面狀態
- 調試失敗的測試

### 2. 使用有頭模式

```bash
npm run test:e2e:headed
```

在可見的瀏覽器窗口中運行測試。

### 3. 運行單個測試

```bash
npx playwright test e2e/example.spec.ts
```

### 4. 調試模式

```bash
# 設置環境變量（Windows PowerShell）
$env:PWDEBUG=1
npx playwright test

# 或使用 --debug 標誌
npx playwright test --debug
```

### 5. 查看測試代碼

所有測試文件位於 `e2e/` 目錄，可以：
- 查看測試邏輯
- 修改測試用例
- 添加新的測試

---

## 📝 測試結果分析

### 測試通過

如果所有測試通過，您會看到：

```
✓ 10 passed (30s)
```

### 測試失敗

如果有測試失敗，需要：
1. 查看錯誤信息
2. 檢查 HTML 報告中的截圖
3. 使用 UI 模式調試
4. 修復代碼或測試

### 生成測試報告

測試完成後，自動生成 HTML 報告：

```bash
npx playwright show-report
```

報告位置：`playwright-report/index.html`

---

## ✅ 測試檢查清單

運行測試前確認：

- [ ] Node.js 和 npm 已安裝
- [ ] 項目依賴已安裝 (`npm install`)
- [ ] Playwright 瀏覽器已安裝 (`npx playwright install`)
- [ ] 端口 3001 未被占用
- [ ] `playwright.config.ts` 配置正確
- [ ] 測試文件存在於 `e2e/` 目錄

---

## 🎯 下一步

1. **運行測試**
   ```bash
   npm run test:e2e
   ```

2. **查看結果**
   ```bash
   npx playwright show-report
   ```

3. **修復問題**（如有）
   - 使用 UI 模式調試
   - 查看錯誤信息
   - 修復代碼或測試

4. **更新文檔**
   - 記錄測試結果
   - 更新測試狀態

---

## 📚 相關文檔

- [Playwright 官方文檔](https://playwright.dev/)
- [測試運行指南](./E2E测试运行指南.md)
- [準備工作總結](../docs/开发笔记/E2E测试准备工作总结.md)

---

**準備狀態**: ✅ 完成  
**最後更新**: 2025-01-28
