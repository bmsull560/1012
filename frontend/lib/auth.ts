/**
 * Secure Authentication Utilities
 * Uses HttpOnly cookies instead of localStorage for token storage
 */

import { cookies } from 'next/headers';

export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
}

/**
 * Set authentication cookies (server-side only)
 * Uses HttpOnly, Secure, and SameSite for maximum security
 */
export async function setAuthCookies(
  accessToken: string,
  refreshToken?: string
): Promise<void> {
  const cookieStore = cookies();
  
  // Access token - short lived (15 minutes)
  cookieStore.set('access_token', accessToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 15 * 60, // 15 minutes
    path: '/',
  });
  
  // Refresh token - longer lived (7 days)
  if (refreshToken) {
    cookieStore.set('refresh_token', refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 7 * 24 * 60 * 60, // 7 days
      path: '/',
    });
  }
}

/**
 * Get access token from cookie (server-side only)
 */
export async function getAccessToken(): Promise<string | null> {
  const cookieStore = cookies();
  return cookieStore.get('access_token')?.value || null;
}

/**
 * Get refresh token from cookie (server-side only)
 */
export async function getRefreshToken(): Promise<string | null> {
  const cookieStore = cookies();
  return cookieStore.get('refresh_token')?.value || null;
}

/**
 * Clear all authentication cookies (logout)
 */
export async function clearAuthCookies(): Promise<void> {
  const cookieStore = cookies();
  cookieStore.delete('access_token');
  cookieStore.delete('refresh_token');
}

/**
 * Check if user is authenticated (has valid access token)
 */
export async function isAuthenticated(): Promise<boolean> {
  const token = await getAccessToken();
  return !!token;
}

/**
 * Validate token format (basic JWT structure check)
 */
export function isValidTokenFormat(token: string): boolean {
  // JWT format: header.payload.signature
  const parts = token.split('.');
  return parts.length === 3;
}

/**
 * Decode JWT payload (without verification - for client-side use only)
 * WARNING: This does NOT verify the signature. Only use for reading claims.
 */
export function decodeJWT(token: string): any {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }
    
    const payload = parts[1];
    const decoded = Buffer.from(payload, 'base64').toString('utf-8');
    return JSON.parse(decoded);
  } catch (error) {
    return null;
  }
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) {
    return true;
  }
  
  const expirationTime = payload.exp * 1000; // Convert to milliseconds
  return Date.now() >= expirationTime;
}

/**
 * Get time until token expires (in seconds)
 */
export function getTokenExpiryTime(token: string): number | null {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) {
    return null;
  }
  
  const expirationTime = payload.exp * 1000;
  const timeRemaining = expirationTime - Date.now();
  return Math.max(0, Math.floor(timeRemaining / 1000));
}
