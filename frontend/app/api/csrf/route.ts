/**
 * CSRF Token API Route
 * Provides CSRF token to client-side code
 */

import { NextRequest, NextResponse } from 'next/server';
import { getClientCsrfToken } from '@/lib/csrf';

export async function GET(request: NextRequest) {
  try {
    // Generate or get existing CSRF token
    const token = await getClientCsrfToken();

    return NextResponse.json({
      token,
    });
  } catch (error) {
    console.error('CSRF token generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate CSRF token' },
      { status: 500 }
    );
  }
}
