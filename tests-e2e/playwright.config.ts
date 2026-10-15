import { defineConfig, devices } from '@playwright/test';

/**
 * Isolated E2E configuration targeting Project Hares Live Production Cluster.
 * Vercel Edge Portal: https://hares-wheat.vercel.app
 * Render API Gateway: https://hares-api.onrender.com
 */
export default defineConfig({
  testDir: './specs',
  timeout: 90000,
  expect: {
    timeout: 35000,
  },
  fullyParallel: false,
  forbidOnly: false,
  retries: 1,
  workers: 1, // Single worker to avoid race conditions or rate limiter collisions
  reporter: [
    ['list'],
    ['html', { outputFolder: 'test-report', open: 'never' }],
  ],
  use: {
    baseURL: 'https://hares-wheat.vercel.app',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
