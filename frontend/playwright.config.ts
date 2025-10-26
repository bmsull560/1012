import { defineConfig, devices } from '@playwright/test';

const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;
const HOST = '127.0.0.1';
const baseURL = process.env.PLAYWRIGHT_TEST_BASE_URL ?? `http://${HOST}:${PORT}`;

export default defineConfig({
  testDir: './tests/ui',
  timeout: 90_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: true,
  reporter: [['list']],
  use: {
    baseURL,
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    viewport: { width: 1280, height: 720 },
    colorScheme: 'light',
    ignoreHTTPSErrors: true,
  },
  webServer: process.env.PLAYWRIGHT_TEST_BASE_URL
    ? undefined
    : {
        command: process.env.CI
          ? 'npm run start -- --hostname 127.0.0.1 --port ' + PORT
          : 'npm run dev -- --hostname 127.0.0.1 --port ' + PORT,
        url: `http://${HOST}:${PORT}`,
        reuseExistingServer: !process.env.CI,
        timeout: 180_000,
      },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
