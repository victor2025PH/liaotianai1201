import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 測試配置
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  /* 測試超時時間 */
  timeout: 30 * 1000,
  /* 每個測試的超時時間 */
  expect: {
    timeout: 5000,
  },
  /* 並行執行 */
  fullyParallel: true,
  /* 失敗時重試 */
  retries: process.env.CI ? 2 : 0,
  /* 並行 worker 數量 */
  workers: process.env.CI ? 1 : undefined,
  /* 報告器配置 */
  reporter: process.env.CI
    ? [['html'], ['github']]
    : [['html'], ['list']],
  /* 共享設置 */
  use: {
    /* 基礎 URL */
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3001',
    /* 收集失敗時的跟踪信息 */
    trace: 'on-first-retry',
    /* 截圖配置 */
    screenshot: 'only-on-failure',
    /* 視頻配置（僅在失敗時保留，WebKit 使用 'off' 以避免路徑問題） */
    video: 'retain-on-failure',
    /* 存儲認證狀態 */
    storageState: undefined, // 可以設置為持久化認證狀態文件
  },

  /* 配置項目 */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        // 禁用視頻錄製以避免路徑過長問題
        video: 'off',
      },
    },

    /* 移動設備測試（可選） */
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],

  /* 本地開發服務器配置 */
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3001',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});

