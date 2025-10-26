import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { disableAnimations } from './utils';
import { capturePercySnapshot } from './percy';

test.describe('Persona wizard experience', () => {
  test.beforeEach(async ({ page }) => {
    await disableAnimations(page);
  });

  async function openPersonaWizard(page: Page) {
    await page.goto('/demo');
    await page.waitForLoadState('networkidle');
    await page.locator('text=Persona-Adaptive Views').first().click();
    await page.locator('text=Beginner').first().click();
    await page.getByRole('button', { name: 'Start Guided Workflow' }).click();
    await expect(page.getByRole('heading', { name: /Step 1 of 5/i })).toBeVisible();
  }

  test('walks users through the guided workflow', async ({ page }) => {
    await openPersonaWizard(page);

    for (let step = 1; step <= 5; step++) {
      await expect(page.getByRole('heading', { name: new RegExp(`Step ${step} of 5`, 'i') })).toBeVisible();
      const cta = page.getByRole('button', { name: step === 5 ? /Finish/i : /Next/i });
      await cta.click();
      if (step < 5) {
        await expect(page.getByRole('heading', { name: new RegExp(`Step ${step + 1} of 5`, 'i') })).toBeVisible();
      }
    }

    await expect(page.getByRole('button', { name: 'Start Guided Workflow' })).toBeVisible();
  });

  test('wizard overlay meets accessibility expectations', async ({ page }) => {
    await openPersonaWizard(page);
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('.fixed.inset-0')
      .analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('captures persona wizard baseline', async ({ page }) => {
    test.skip(!process.env.PERCY_TOKEN, 'Percy token not configured');
    await openPersonaWizard(page);
    await capturePercySnapshot(page, 'Persona wizard overlay');
  });
});
