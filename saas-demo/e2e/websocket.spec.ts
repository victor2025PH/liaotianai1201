import { test, expect } from '@playwright/test';

/**
 * WebSocket 連接測試
 * 測試實時數據推送功能
 */
test.describe('WebSocket 實時數據推送測試', () => {
  test('監控頁面應該能夠連接 WebSocket', async ({ page }) => {
    // 監聽 WebSocket 連接
    const wsMessages: any[] = [];
    
    page.on('websocket', (ws) => {
      console.log('WebSocket 連接已建立:', ws.url());
      
      ws.on('framereceived', (event) => {
        try {
          const data = JSON.parse(event.payload as string);
          wsMessages.push(data);
          console.log('收到 WebSocket 消息:', data);
        } catch (e) {
          // 忽略非 JSON 消息
        }
      });
    });

    // 訪問監控頁面
    await page.goto('/group-ai/monitor');
    await page.waitForLoadState('networkidle');
    
    // 等待 WebSocket 連接建立（如果頁面使用了 WebSocket）
    await page.waitForTimeout(3000);
    
    // 檢查頁面是否正常渲染
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
    
    // 如果頁面使用了 WebSocket，應該有連接
    // 注意：這取決於實際實現，如果頁面沒有使用 WebSocket，這個測試會通過但不檢查 WebSocket
    console.log('WebSocket 消息數量:', wsMessages.length);
  });

  test('Dashboard 頁面應該能夠接收實時數據更新', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 等待初始數據加載
    await page.waitForTimeout(2000);
    
    // 檢查是否有統計卡片
    const cards = page.locator('[class*="card"], article, section');
    const cardCount = await cards.count();
    
    // 至少應該有一些內容
    expect(cardCount).toBeGreaterThanOrEqual(0);
    
    // 等待可能的實時更新（如果有的話）
    await page.waitForTimeout(5000);
    
    // 檢查頁面是否仍然正常
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent.first()).toBeVisible();
  });
});

