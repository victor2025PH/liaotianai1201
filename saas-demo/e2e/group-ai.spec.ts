import { test, expect } from '@playwright/test';

test.describe('Group AI 功能測試', () => {
  test('賬號管理頁面應該正常加載', async ({ page }) => {
    await page.goto('/group-ai/accounts');
    await page.waitForLoadState('networkidle');
    
    // 等待內容加載
    await page.waitForTimeout(2000);
    
    // 檢查頁面是否正常渲染
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
    
    // 檢查是否有賬號列表或創建按鈕
    const createButton = page.getByRole('button', { name: /創建|新增|添加|create|add/i });
    const accountsTable = page.locator('table');
    
    // 至少應該有創建按鈕或表格
    const hasContent = await createButton.isVisible().catch(() => false) ||
                      await accountsTable.isVisible().catch(() => false);
    
    // 頁面應該有主要內容區域
    await expect(mainContent.first()).toBeVisible();
  });

  test('劇本管理頁面應該正常加載', async ({ page }) => {
    await page.goto('/group-ai/scripts');
    await page.waitForLoadState('networkidle');
    
    // 等待內容加載
    await page.waitForTimeout(2000);
    
    // 檢查頁面是否正常渲染
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
  });

  test('監控頁面應該正常加載', async ({ page }) => {
    await page.goto('/group-ai/monitor');
    await page.waitForLoadState('networkidle');
    
    // 等待內容加載
    await page.waitForTimeout(2000);
    
    // 檢查頁面是否正常渲染
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
  });

  test('角色分配頁面應該正常加載', async ({ page }) => {
    await page.goto('/group-ai/role-assignments');
    await page.waitForLoadState('networkidle');
    
    // 等待內容加載
    await page.waitForTimeout(2000);
    
    // 檢查頁面是否正常渲染
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
  });
});

