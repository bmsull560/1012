import type { Page } from '@playwright/test';

const AUTH_STORAGE_KEY = 'auth-storage';

export async function primeAuthState(page: Page) {
  await page.addInitScript(({ storageKey }) => {
    try {
      const state = {
        state: {
          isAuthenticated: true,
          user: {
            id: 'test-user',
            email: 'tester@example.com',
            first_name: 'Test',
            last_name: 'User',
            expertiseLevel: 'expert',
            preferences: {
              theme: 'light',
              dataGranularity: 'summary',
              showFormulas: true,
              enableNotifications: true,
            },
          },
          token: 'test-token',
          refreshToken: 'test-refresh-token',
        },
        version: 0,
      };
      window.localStorage.setItem(storageKey, JSON.stringify(state));
    } catch (error) {
      console.warn('Failed to prime auth state', error);
    }
  }, { storageKey: AUTH_STORAGE_KEY });
}

export async function stubWorkspaceNetwork(page: Page) {
  await page.route('**/socket.io/**', (route) => route.abort());

  const mockAgentResponse = {
    id: 'mock-response',
    agent: 'value-architect',
    content: {
      message: 'Mock response from Value Architect',
      total_potential_value: 1250000,
      value_drivers: [
        { name: 'Automation', potential_value: 750000 },
        { name: 'Efficiency', potential_value: 500000 },
      ],
      confidence_score: 0.82,
    },
    status: 'success',
  };

  await page.route('http://localhost:8011/**', async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgentResponse),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok' }),
    });
  });

  for (const port of [8012, 8013, 8014]) {
    await page.route(`http://localhost:${port}/**`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAgentResponse),
      }),
    );
  }
}

export async function disableAnimations(page: Page) {
  await page.addInitScript(() => {
    const style = document.createElement('style');
    style.innerHTML = `
      *, *::before, *::after {
        transition-duration: 0s !important;
        animation-duration: 0s !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
      }
    `;
    document.head.appendChild(style);
  });
}

export async function prepareWorkspace(page: Page) {
  await disableAnimations(page);
  await primeAuthState(page);
  await stubWorkspaceNetwork(page);
}
