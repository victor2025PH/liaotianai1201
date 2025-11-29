# E2E 測試修復說明

> **更新日期**: 2025-01-28

---

## ✅ 已完成的工作

### 1. 創建認證輔助系統

已創建完整的認證輔助系統：

- **`e2e/helpers/auth.ts`** - 認證輔助函數
  - 支持 UI 登錄和 API 登錄
  - 自動檢測登錄狀態
  - 提供便捷的登錄函數

- **`e2e/fixtures.ts`** - 測試 Fixtures
  - 擴展 Playwright fixtures
  - 提供 `authenticatedPage` 自動登錄頁面

### 2. 修復示例測試

- ✅ 更新 `e2e/example.spec.ts`
- ✅ 添加自動登錄
- ✅ 修復頁面標題期望值

### 3. 優化配置

- ✅ 禁用 WebKit 視頻錄製（避免路徑問題）
- ✅ 添加存儲狀態支持

---

## 🔧 如何使用

### 方法 1: 使用 authenticatedPage fixture（推薦）

```typescript
import { test, expect } from './fixtures';

test('我的測試', async ({ authenticatedPage }) => {
  // authenticatedPage 已自動登錄
  await authenticatedPage.goto('/dashboard');
  // ... 測試邏輯
});
```

### 方法 2: 在 beforeEach 中登錄

```typescript
import { test, expect } from './fixtures';
import { ensureLoggedIn } from './helpers/auth';

test.describe('測試組', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });
  
  test('我的測試', async ({ page }) => {
    await page.goto('/dashboard');
    // ... 測試邏輯
  });
});
```

---

## 📋 待修復的測試文件

以下文件需要添加登錄支持：

1. `e2e/dashboard.spec.ts`
2. `e2e/navigation.spec.ts`
3. `e2e/pages.spec.ts`
4. `e2e/accounts-management.spec.ts`
5. `e2e/api-interaction.spec.ts`
6. `e2e/data-sync.spec.ts`
7. `e2e/group-ai.spec.ts`
8. `e2e/monitor-dashboard.spec.ts`
9. `e2e/websocket.spec.ts`

---

## 🚀 快速修復模板

對於每個測試文件，執行以下修改：

### 1. 更新導入

```typescript
// 將這行
import { test, expect } from '@playwright/test';

// 改為
import { test, expect } from './fixtures';
import { ensureLoggedIn } from './helpers/auth';
```

### 2. 添加 beforeEach

```typescript
test.describe('測試組', () => {
  test.beforeEach(async ({ page }) => {
    await ensureLoggedIn(page);
  });
  
  // 原有測試用例...
});
```

### 3. 更新頁面標題檢查（如適用）

```typescript
// 將這行
await expect(page).toHaveTitle(/Smart TG Admin/i);

// 改為
await expect(page).toHaveTitle(/聊天 AI 控制台|Smart TG Admin/i);
```

---

## ⚙️ 配置測試帳號

如果測試帳號密碼不同，編輯 `e2e/helpers/auth.ts`:

```typescript
const DEFAULT_TEST_CREDENTIALS = {
  username: 'admin@example.com',
  password: 'your-test-password', // 修改這裡
};
```

---

## 🔍 驗證修復

修復後，重新運行測試：

```bash
cd saas-demo
npm run test:e2e
```

查看結果，預期通過率應該大幅提升。

---

**狀態**: ✅ 輔助系統已就緒，等待批量更新測試文件
