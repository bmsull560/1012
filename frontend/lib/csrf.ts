/**
 * CSRF Protection Utilities
 * Implements Cross-Site Request Forgery protection
 */

import { cookies } from 'next/headers';
import crypto from 'crypto';

const CSRF_TOKEN_NAME = 'csrf_token';
const CSRF_HEADER_NAME = 'X-CSRF-Token';

/**
 * Generate a cryptographically secure CSRF token
 */
export function generateCsrfToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

/**
 * Set CSRF token in HttpOnly cookie (server-side)
 */
export async function setCsrfToken(): Promise<string> {
  const token = generateCsrfToken();
  const cookieStore = cookies();
  
  cookieStore.set(CSRF_TOKEN_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 60 * 60, // 1 hour
    path: '/',
  });
  
  return token;
}

/**
 * Get CSRF token from cookie (server-side)
 */
export async function getCsrfToken(): Promise<string | null> {
  const cookieStore = cookies();
  return cookieStore.get(CSRF_TOKEN_NAME)?.value || null;
}

/**
 * Validate CSRF token (server-side)
 */
export async function validateCsrfToken(token: string): Promise<boolean> {
  const storedToken = await getCsrfToken();
  
  if (!storedToken || !token) {
    return false;
  }
  
  // Use timing-safe comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(storedToken),
    Buffer.from(token)
  );
}

/**
 * Clear CSRF token
 */
export async function clearCsrfToken(): Promise<void> {
  const cookieStore = cookies();
  cookieStore.delete(CSRF_TOKEN_NAME);
}

/**
 * Get CSRF token for client-side use
 * This returns a non-HttpOnly cookie that JavaScript can read
 */
export async function getClientCsrfToken(): Promise<string> {
  const cookieStore = cookies();
  let token = cookieStore.get(`${CSRF_TOKEN_NAME}_client`)?.value;
  
  if (!token) {
    token = generateCsrfToken();
    cookieStore.set(`${CSRF_TOKEN_NAME}_client`, token, {
      httpOnly: false, // Allow JavaScript to read
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 60 * 60, // 1 hour
      path: '/',
    });
  }
  
  return token;
}

/**
 * Middleware to validate CSRF token on state-changing requests
 */
export async function validateCsrfMiddleware(
  request: Request
): Promise<{ valid: boolean; error?: string }> {
  const method = request.method;
  
  // Only validate on state-changing methods
  if (!['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    return { valid: true };
  }
  
  // Get token from header
  const headerToken = request.headers.get(CSRF_HEADER_NAME);
  
  if (!headerToken) {
    return {
      valid: false,
      error: 'CSRF token missing from request headers',
    };
  }
  
  // Validate token
  const isValid = await validateCsrfToken(headerToken);
  
  if (!isValid) {
    return {
      valid: false,
      error: 'Invalid CSRF token',
    };
  }
  
  return { valid: true };
}

/**
 * Get CSRF token from client-side cookie
 * Use this in client-side code to get the token for API requests
 */
export function getClientCsrfTokenFromCookie(): string | null {
  if (typeof document === 'undefined') {
    return null;
  }
  
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === `${CSRF_TOKEN_NAME}_client`) {
      return decodeURIComponent(value);
    }
  }
  
  return null;
}
