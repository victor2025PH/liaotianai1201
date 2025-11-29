# E2E 測試修復計劃

> **日期**: 2025-01-28  
> **狀態**: 🔄 進行中

---

## 🔍 問題總結

### 測試結果
- **通過**: 32 個 (26.7%)
- **失敗**: 88 個 (73.3%)
- **總數**: 120 個測試

### 主要問題

1. 🔴 **認證問題** - 測試未處理登錄流程
2. 🟡 **頁面標題不匹配** - 期望值與實際不符
3. 🟡 **元素選擇器問題** - 找不到 main 元素
4. 🟢 **WebKit 視頻錄製問題** - 路徑過長

---

## ✅ 已完成的修復

### 1. 創建認證輔助函數
- ✅ `e2e/helpers/auth.ts` - 登錄 helper 函數
  - `loginUser()` - UI 登錄
  - `loginViaAPI()` - API 直接登錄（更快）
  - `ensureLoggedIn()` - 確保已登錄
  - `isLoggedIn()` - 檢查登錄狀態

### 2. 創建測試 Fixtures
- ✅ `e2e/fixtures.ts` - 擴展 Playwright fixtures
  - `authenticatedPage` - 自動登錄的頁面 fixture

### 3. 修復示例測試
- ✅ 更新 `example.spec.ts`
  - 添加 beforeEach 自動登錄
  - 修復頁面標題期望值

### 4. 優化配置
- ✅ 禁用 WebKit 視頻錄製
- ✅ 配置存儲狀態支持

---

## ⏳ 待完成的修復

### 1. 更新所有測試文件

需要更新以下測試文件，添加登錄支持：

- [ ] `e2e/dashboard.spec.ts`
- [ ] `e2e/navigation.spec.ts`
- [ ] `e2e/pages.spec.ts`
- [ ] `e2e/accounts-management.spec.ts`
- [ ] `e2e/api-interaction.spec.ts`
- [ ] `e2e/data-sync.spec.ts`
- [ ] `e2e/group-ai.spec.ts`
- [ ] `e2e/monitor-dashboard.spec.ts`
- [ ] `e2e/websocket.spec.ts`

### 2. 確認測試帳號密碼

需要確認測試環境中的實際密碼：
- 選項 1: `testpass123`（與後端測試一致）
- 選項 2: `changeme123`（前端默認值）

### 3. 驗證元素選擇器

檢查實際頁面結構，確保選擇器正確。

---

## 🚀 快速修復腳本

可以批量更新所有測試文件，添加：

```typescript
import { test, expect } from './fixtures';
import { ensureLoggedIn } from './helpers/auth';

test.describe('測試組', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });
  // ... 測試用例
});
```

---

## 📋 下一步行動

1. ✅ 創建認證輔助函數
2. ✅ 創建測試 fixtures
3. ✅ 修復示例測試
4. ⏳ 批量更新其他測試文件
5. ⏳ 確認測試帳號密碼
6. ⏳ 重新運行測試驗證

---

**狀態**: 🔄 修復中  
**下次更新**: 批量更新完成後
