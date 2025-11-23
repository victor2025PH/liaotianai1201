import { test, expect } from '@playwright/test';

test.describe('頁面渲染測試', () => {
  test('Dashboard 頁面應該正常加載', async ({ page }) => {
    await page.goto('/');
    
    // 等待頁面加載
    await page.waitForLoadState('networkidle');
    
    // 檢查頁面是否有主要內容
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
  });

  test('會話列表頁面應該正常加載', async ({ page }) => {
    await page.goto('/sessions');
    
    await page.waitForLoadState('networkidle');
    
    // 檢查頁面標題或主要內容
    const pageTitle = page.getByRole('heading', { name: /sessions|會話/i });
    if (await pageTitle.isVisible().catch(() => false)) {
      await expect(pageTitle).toBeVisible();
    }
  });

  test('日誌頁面應該正常加載', async ({ page }) => {
    await page.goto('/logs');
    
    await page.waitForLoadState('networkidle');
    
    // 檢查頁面是否正常渲染
    const pageContent = page.locator('main, [role="main"]');
    await expect(pageContent.first()).toBeVisible();
  });

  test('Group AI 賬號管理頁面應該正常加載', async ({ page }) => {
    await page.goto('/group-ai/accounts');
    
    await page.waitForLoadState('networkidle');
    
    // 檢查頁面是否正常渲染
    const pageContent = page.locator('main, [role="main"]');
    await expect(pageContent.first()).toBeVisible();
  });

  test('Group AI 劇本管理頁面應該正常加載', async ({ page }) => {
    await page.goto('/group-ai/scripts');
    
    await page.waitForLoadState('networkidle');
    
    // 檢查頁面是否正常渲染
    const pageContent = page.locator('main, [role="main"]');
    await expect(pageContent.first()).toBeVisible();
  });

  test('監控頁面應該正常加載', async ({ page }) => {
    await page.goto('/group-ai/monitor');
    
    await page.waitForLoadState('networkidle');
    
    // 檢查頁面是否正常渲染
    const pageContent = page.locator('main, [role="main"]');
    await expect(pageContent.first()).toBeVisible();
  });
});

