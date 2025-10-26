/**
 * Login API Route
 * Handles authentication and sets HttpOnly cookies
 */

import { NextRequest, NextResponse } from 'next/server';
import { setAuthCookies } from '@/lib/auth';
import { validateCsrfMiddleware } from '@/lib/csrf';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Validate CSRF token
    const csrfValidation = await validateCsrfMiddleware(request);
    if (!csrfValidation.valid) {
      return NextResponse.json(
        { error: csrfValidation.error || 'CSRF validation failed' },
        { status: 403 }
      );
    }

    const body = await request.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Create FormData for backend authentication
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    // Call backend authentication endpoint
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.detail || 'Authentication failed' },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Set HttpOnly cookies with tokens
    await setAuthCookies(data.access_token, data.refresh_token);

    // Return success without tokens in response body
    return NextResponse.json({
      success: true,
      user: data.user,
    });
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
