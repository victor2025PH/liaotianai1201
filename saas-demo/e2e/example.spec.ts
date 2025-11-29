import { test, expect } from '@playwright/test';
import { ensureLoggedIn } from './helpers/auth';

test.describe('示例 E2E 測試', () => {
  test.beforeEach(async ({ page }) => {
    // 確保用戶已登錄
    await ensureLoggedIn(page);
  });

  test('應該顯示首頁', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 檢查頁面標題（更新為實際標題）
    await expect(page).toHaveTitle(/聊天 AI 控制台|Smart TG Admin/i);
  });

  test('應該能夠導航到不同頁面', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 檢查導航元素是否存在（登錄後應該有導航）
    const navigation = page.locator('nav, [role="navigation"], aside, header');
    const navCount = await navigation.count();
    
    // 至少有導航元素或頁面已渲染
    expect(navCount).toBeGreaterThan(0);
  });
});

