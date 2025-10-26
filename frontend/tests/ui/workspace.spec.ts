import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { prepareWorkspace } from './utils';
import { capturePercySnapshot } from './percy';

test.describe('Unified workspace experience', () => {
  test.beforeEach(async ({ page }) => {
    await prepareWorkspace(page);
  });

  test('renders conversation tools and agent selector', async ({ page }) => {
    await page.goto('/workspace');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'Conversations' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'New Conversation' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Value Architect' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Value Committer' })).toBeVisible();
  });

  test('allows sending a prompt to the active agent', async ({ page }) => {
    await page.goto('/workspace');
    await page.waitForLoadState('networkidle');

    const prompt = 'Draft a value hypothesis for Helios Co.';
    const input = page.getByPlaceholder(/Ask Value Architect anything/i);
    await input.fill(prompt);
    await page.getByRole('button', { name: 'Send' }).click();

    await expect(page.getByText(prompt)).toBeVisible();
    await expect(page.getByText('Mock response from Value Architect')).toBeVisible({ timeout: 4000 });
  });

  test('workspace view has no accessibility violations', async ({ page }) => {
    await page.goto('/workspace');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('captures workspace baseline', async ({ page }) => {
    test.skip(!process.env.PERCY_TOKEN, 'Percy token not configured');
    await page.goto('/workspace');
    await page.waitForLoadState('networkidle');
    await capturePercySnapshot(page, 'Workspace - conversation view');
  });
});
