import type { Page } from '@playwright/test';

let snapshot: ((page: Page, name: string) => Promise<void>) | null = null;

export async function capturePercySnapshot(page: Page, name: string) {
  if (!process.env.PERCY_TOKEN) {
    return;
  }

  if (!snapshot) {
    const percy = await import('@percy/playwright');
    snapshot = percy.percySnapshot;
  }

  await snapshot(page, name);
}
