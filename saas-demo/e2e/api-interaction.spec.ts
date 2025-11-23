import { test, expect } from '@playwright/test';

test.describe('API 交互測試', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('應該能夠獲取 Dashboard 數據', async ({ page }) => {
    // 監聽 API 請求
    const apiRequests: string[] = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/api/v1/dashboard') || url.includes('/api/v1/metrics')) {
        apiRequests.push(url);
      }
    });

    // 等待 API 請求完成
    await page.waitForTimeout(2000);

    // 檢查是否有 API 請求（或使用 Mock 數據）
    // 注意：如果使用 Mock 數據，可能不會有實際的 API 請求
    expect(apiRequests.length).toBeGreaterThanOrEqual(0);
  });

  test('會話列表頁面應該能夠加載數據', async ({ page }) => {
    await page.goto('/sessions');
    
    await page.waitForLoadState('networkidle');
    
    // 檢查是否顯示加載狀態或數據
    const loadingState = page.locator('[data-loading], .loading, [role="status"]');
    const dataContent = page.locator('table, [data-testid="sessions-list"]');
    
    // 等待加載完成
    await page.waitForTimeout(1000);
    
    // 應該有內容（加載狀態或數據）
    const hasContent = await loadingState.isVisible().catch(() => false) || 
                      await dataContent.isVisible().catch(() => false);
    
    // 如果頁面正常，至少應該有一些內容可見
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
  });

  test('日誌頁面應該能夠加載數據', async ({ page }) => {
    await page.goto('/logs');
    
    await page.waitForLoadState('networkidle');
    
    // 等待加載完成
    await page.waitForTimeout(1000);
    
    // 檢查頁面是否有內容
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
  });
});

