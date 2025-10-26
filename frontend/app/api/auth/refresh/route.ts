/**
 * Token Refresh API Route
 * Refreshes access token using refresh token from HttpOnly cookie
 */

import { NextRequest, NextResponse } from 'next/server';
import { getRefreshToken, setAuthCookies, clearAuthCookies } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Get refresh token from HttpOnly cookie
    const refreshToken = await getRefreshToken();

    if (!refreshToken) {
      return NextResponse.json(
        { error: 'No refresh token available' },
        { status: 401 }
      );
    }

    // Call backend refresh endpoint
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    if (!response.ok) {
      // Refresh failed, clear cookies
      await clearAuthCookies();
      return NextResponse.json(
        { error: 'Token refresh failed' },
        { status: 401 }
      );
    }

    const data = await response.json();

    // Set new tokens in HttpOnly cookies
    await setAuthCookies(data.access_token, data.refresh_token);

    return NextResponse.json({
      success: true,
    });
  } catch (error) {
    console.error('Token refresh error:', error);
    await clearAuthCookies();
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
