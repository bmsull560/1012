import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { tenantMiddleware } from './middleware/tenant';

export function middleware(request: NextRequest) {
  // Apply tenant middleware
  return tenantMiddleware(request);
}

// Configure which routes use middleware
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\..*|public).*)',
  ],
};
