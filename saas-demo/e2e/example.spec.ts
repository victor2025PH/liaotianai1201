import { test, expect } from '@playwright/test';

test.describe('示例 E2E 測試', () => {
  test('應該顯示首頁', async ({ page }) => {
    await page.goto('/');
    
    // 檢查頁面標題
    await expect(page).toHaveTitle(/Smart TG Admin/i);
  });

  test('應該能夠導航到不同頁面', async ({ page }) => {
    await page.goto('/');
    
    // 檢查導航元素是否存在
    const navigation = page.locator('nav');
    await expect(navigation).toBeVisible();
  });
});

