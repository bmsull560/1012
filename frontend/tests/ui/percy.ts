import type { Page } from '@playwright/test';

let snapshot: ((page: Page, name: string) => Promise<void>) | null = null;

export async function capturePercySnapshot(page: Page, name: string) {
  if (!process.env.PERCY_TOKEN) {
    return;
  }

  if (!snapshot) {
    try {
      const percy = await import('@percy/playwright');
      // support both named and default exports, or the module itself being the function
      const fn = (percy as any).percySnapshot ?? (percy as any).default ?? (percy as any);
      if (typeof fn === 'function') {
        snapshot = fn;
      } else {
        // module didn't provide a usable snapshot function; skip silently
        return;
      }
    } catch {
      // failed to load Percy library; skip snapshot to avoid failing tests
      return;
    }
  }

  if (!snapshot) {
    return;
  }

  await snapshot(page, name);
}
