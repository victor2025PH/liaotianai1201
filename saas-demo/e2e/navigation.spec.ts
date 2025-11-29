import { test, expect } from '@playwright/test';
import { ensureLoggedIn } from './helpers/auth';

test.describe('導航測試', () => {
  test.beforeEach(async ({ page }) => {
    // 確保用戶已登錄
    await ensureLoggedIn(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('應該能夠導航到 Dashboard', async ({ page }) => {
    // 查找並點擊 Dashboard 鏈接
    const dashboardLink = page.getByRole('link', { name: /dashboard|儀表板/i });
    if (await dashboardLink.isVisible()) {
      await dashboardLink.click();
      await expect(page).toHaveURL(/.*\/$/);
    }
  });

  test('應該能夠導航到會話列表', async ({ page }) => {
    const sessionsLink = page.getByRole('link', { name: /sessions|會話/i });
    if (await sessionsLink.isVisible()) {
      await sessionsLink.click();
      await expect(page).toHaveURL(/.*\/sessions/);
    }
  });

  test('應該能夠導航到日誌頁面', async ({ page }) => {
    const logsLink = page.getByRole('link', { name: /logs|日誌/i });
    if (await logsLink.isVisible()) {
      await logsLink.click();
      await expect(page).toHaveURL(/.*\/logs/);
    }
  });

  test('應該能夠導航到 Group AI 賬號管理', async ({ page }) => {
    const accountsLink = page.getByRole('link', { name: /accounts|賬號|賬戶/i });
    if (await accountsLink.isVisible()) {
      await accountsLink.click();
      await expect(page).toHaveURL(/.*\/group-ai\/accounts/);
    }
  });
});

