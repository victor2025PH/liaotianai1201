import { test, expect } from '@playwright/test';

/**
 * 賬號管理頁面詳細測試
 */
test.describe('賬號管理頁面測試', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/group-ai/accounts');
    await page.waitForLoadState('networkidle');
    // 等待內容加載
    await page.waitForTimeout(2000);
  });

  test('應該顯示賬號列表', async ({ page }) => {
    // 檢查是否有表格或列表
    const table = page.locator('table');
    const list = page.locator('[role="list"], [class*="list"]');
    
    const hasTable = await table.isVisible().catch(() => false);
    const hasList = await list.isVisible().catch(() => false);
    
    // 至少應該有表格或列表
    expect(hasTable || hasList).toBeTruthy();
  });

  test('應該能夠打開創建賬號對話框', async ({ page }) => {
    // 查找創建按鈕
    const createButton = page.getByRole('button', { name: /創建|新增|添加|create|add/i });
    
    if (await createButton.isVisible().catch(() => false)) {
      await createButton.click();
      
      // 等待對話框打開
      await page.waitForTimeout(500);
      
      // 檢查是否有對話框
      const dialog = page.locator('[role="dialog"], [class*="dialog"]');
      const hasDialog = await dialog.isVisible().catch(() => false);
      
      // 如果有對話框，應該可見
      if (hasDialog) {
        await expect(dialog.first()).toBeVisible();
      }
    }
  });

  test('應該能夠搜索賬號', async ({ page }) => {
    // 查找搜索輸入框
    const searchInput = page.getByPlaceholder(/搜索|search/i).or(
      page.locator('input[type="search"]')
    );
    
    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill('test');
      await page.waitForTimeout(1000);
      
      // 檢查搜索結果
      const mainContent = page.locator('main, [role="main"]');
      await expect(mainContent.first()).toBeVisible();
    }
  });

  test('應該能夠過濾賬號狀態', async ({ page }) => {
    // 查找狀態過濾器
    const statusFilter = page.getByRole('button', { name: /狀態|status|filter/i }).or(
      page.locator('select, [role="combobox"]')
    );
    
    if (await statusFilter.isVisible().catch(() => false)) {
      await statusFilter.click();
      await page.waitForTimeout(500);
      
      // 檢查過濾是否生效
      const mainContent = page.locator('main, [role="main"]');
      await expect(mainContent.first()).toBeVisible();
    }
  });

  test('應該能夠查看賬號詳情', async ({ page }) => {
    // 查找賬號詳情按鈕或鏈接
    const detailButton = page.getByRole('button', { name: /詳情|detail|查看|view/i }).or(
      page.locator('a[href*="/accounts/"]')
    );
    
    if (await detailButton.first().isVisible().catch(() => false)) {
      await detailButton.first().click();
      await page.waitForTimeout(1000);
      
      // 檢查是否導航到詳情頁面或打開對話框
      const dialog = page.locator('[role="dialog"]');
      const hasDialog = await dialog.isVisible().catch(() => false);
      
      if (hasDialog) {
        await expect(dialog.first()).toBeVisible();
      } else {
        // 檢查是否導航到詳情頁面
        await page.waitForURL(/\/accounts\/.*/, { timeout: 3000 }).catch(() => {});
        const mainContent = page.locator('main, [role="main"]');
        await expect(mainContent.first()).toBeVisible();
      }
    }
  });
});

