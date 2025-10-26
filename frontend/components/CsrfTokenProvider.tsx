/**
 * CSRF Token Provider
 * Fetches and maintains CSRF token for the application
 */

'use client';

import { useEffect } from 'react';

export function CsrfTokenProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Fetch CSRF token on mount
    const fetchCsrfToken = async () => {
      try {
        const response = await fetch('/api/csrf');
        if (response.ok) {
          const data = await response.json();
          // Token is automatically set in cookie by the API route
          console.log('CSRF token initialized');
        }
      } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
      }
    };

    fetchCsrfToken();

    // Refresh token every 30 minutes
    const interval = setInterval(fetchCsrfToken, 30 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return <>{children}</>;
}
