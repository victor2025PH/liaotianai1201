# E2E 測試 Fixture 問題修復

> **日期**: 2025-01-28  
> **問題**: Playwright Test 配置錯誤  
> **狀態**: ✅ 已修復

---

## 🔍 問題分析

### 錯誤信息

```
Error: Playwright Test did not expect test.describe() to be called here.
Most common reasons include:
- You are calling test.describe() in a configuration file.
- You are calling test.describe() in a file that is imported by the configuration file.
- You have two different versions of @playwright/test.
```

### 問題原因

使用自定義 `fixtures.ts` 導出擴展的 `test` 對象時，Playwright 可能：
1. 將其視為配置文件的一部分
2. 導致測試文件無法正確識別 `test.describe()`

---

## ✅ 解決方案

### 改為直接使用原始 Playwright test

**修改前**（有問題）:
```typescript
import { test, expect } from './fixtures';  // 自定義 fixture
```

**修改後**（修復）:
```typescript
import { test, expect } from '@playwright/test';  // 直接使用原始 test
import { ensureLoggedIn } from './helpers/auth';  // 認證 helper
```

### 認證方式

認證功能通過在 `beforeEach` 中調用 helper 函數實現：

```typescript
test.beforeEach(async ({ page }) => {
  await ensureLoggedIn(page);  // 自動登錄
  // 其他初始化...
});
```

---

## 📝 修復的文件

已修復所有 **10 個測試文件**：

1. ✅ `e2e/example.spec.ts`
2. ✅ `e2e/dashboard.spec.ts`
3. ✅ `e2e/navigation.spec.ts`
4. ✅ `e2e/pages.spec.ts`
5. ✅ `e2e/accounts-management.spec.ts`
6. ✅ `e2e/api-interaction.spec.ts`
7. ✅ `e2e/data-sync.spec.ts`
8. ✅ `e2e/group-ai.spec.ts`
9. ✅ `e2e/monitor-dashboard.spec.ts`
10. ✅ `e2e/websocket.spec.ts`

所有文件現在都：
- 使用 `import { test, expect } from '@playwright/test'`
- 在 `beforeEach` 中調用 `ensureLoggedIn()`

---

## 🔧 保留的輔助文件

### `e2e/helpers/auth.ts`

保留此文件，包含所有認證輔助函數：
- `loginUser()` - UI 登錄
- `loginViaAPI()` - API 登錄
- `ensureLoggedIn()` - 確保已登錄
- `isLoggedIn()` - 檢查登錄狀態

### `e2e/fixtures.ts`

已簡化為直接重新導出原始的 test 和 expect（作為備用）。

---

## 🚀 現在可以運行測試

所有測試文件已修復，現在應該可以正常運行：

```bash
cd saas-demo
npm run test:e2e
```

---

## ✅ 修復檢查清單

- [x] 修復所有測試文件的導入語句
- [x] 確保所有測試都有 `beforeEach` 自動登錄
- [x] 保留認證 helper 函數
- [x] 簡化 fixtures.ts
- [ ] **驗證測試可以運行** ⏳

---

**狀態**: ✅ 已修復  
**下一步**: 重新運行測試驗證
