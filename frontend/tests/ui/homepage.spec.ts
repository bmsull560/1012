import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { disableAnimations } from './utils';
import { capturePercySnapshot } from './percy';

test.describe('Homepage experience', () => {
  test.beforeEach(async ({ page }) => {
    await disableAnimations(page);
  });

  test('displays hero content and statistics', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { level: 1, name: /Transform Customer Value/ })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Get Started' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Watch Demo' })).toBeVisible();
    await expect(page.getByText('Enterprise-Grade B2B Value Platform')).toBeVisible();
    await expect(page.getByText('Value Accuracy').first()).toBeVisible();
  });

  test('redirects unauthenticated users to login when starting', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Get Started' }).click();
    await page.waitForURL('**/auth/login');
    await expect(page.getByRole('heading', { level: 1, name: /Welcome back/i })).toBeVisible();
  });

  test('has no critical accessibility regressions', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('captures visual baseline', async ({ page }) => {
    test.skip(!process.env.PERCY_TOKEN, 'Percy token not configured');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await capturePercySnapshot(page, 'Homepage - hero');
  });
});
