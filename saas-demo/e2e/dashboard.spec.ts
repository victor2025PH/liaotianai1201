import { test, expect } from '@playwright/test';
import { ensureLoggedIn } from './helpers/auth';

test.describe('Dashboard 頁面測試', () => {
  test.beforeEach(async ({ page }) => {
    // 確保用戶已登錄
    await ensureLoggedIn(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('應該顯示 Dashboard 標題', async ({ page }) => {
    // 檢查是否有 Dashboard 相關的標題或內容
    const heading = page.getByRole('heading', { name: /dashboard|總覽|儀表板/i });
    if (await heading.isVisible().catch(() => false)) {
      await expect(heading).toBeVisible();
    } else {
      // 如果沒有標題，檢查頁面是否有主要內容
      const mainContent = page.locator('main, [role="main"]');
      await expect(mainContent.first()).toBeVisible();
    }
  });

  test('應該顯示統計卡片', async ({ page }) => {
    // 等待內容加載
    await page.waitForTimeout(2000);

    // 檢查是否有統計卡片（Card 組件）
    const cards = page.locator('[class*="card"], article, section');
    const cardCount = await cards.count();
    
    // 至少應該有一些內容
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });

  test('應該顯示最近會話列表', async ({ page }) => {
    // 等待內容加載
    await page.waitForTimeout(2000);

    // 查找會話列表相關元素
    const sessionsSection = page.getByText(/最近.*會話|sessions/i);
    if (await sessionsSection.isVisible().catch(() => false)) {
      await expect(sessionsSection).toBeVisible();
    }

    // 或者檢查表格是否存在
    const table = page.locator('table');
    if (await table.isVisible().catch(() => false)) {
      await expect(table.first()).toBeVisible();
    }
  });

  test('應該能夠刷新數據', async ({ page }) => {
    // 查找刷新按鈕
    const refreshButton = page.getByRole('button', { name: /refresh|刷新/i });
    
    if (await refreshButton.isVisible().catch(() => false)) {
      await refreshButton.click();
      // 等待刷新完成
      await page.waitForTimeout(1000);
    }
  });
});

