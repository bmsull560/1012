import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Tenant identification and isolation middleware
export function tenantMiddleware(request: NextRequest) {
  const url = request.nextUrl.clone();
  const hostname = request.headers.get('host') || '';
  
  // Extract tenant from subdomain (e.g., acme.valueverse.ai)
  const subdomain = hostname.split('.')[0];
  const isSubdomain = hostname.includes('.') && !hostname.startsWith('www.');
  
  // Get tenant from various sources
  let tenantId: string | null = null;
  
  // 1. Check subdomain
  if (isSubdomain && subdomain !== 'app' && subdomain !== 'api') {
    tenantId = subdomain;
  }
  
  // 2. Check custom header
  const headerTenantId = request.headers.get('x-tenant-id');
  if (headerTenantId) {
    tenantId = headerTenantId;
  }
  
  // 3. Check URL path (for admin routes)
  const pathMatch = url.pathname.match(/^\/tenant\/([^\/]+)/);
  if (pathMatch) {
    tenantId = pathMatch[1];
  }
  
  // 4. Check cookie (for persistent tenant context)
  const cookieTenantId = request.cookies.get('tenant_id')?.value;
  if (cookieTenantId && !tenantId) {
    tenantId = cookieTenantId;
  }
  
  // Create response with tenant context
  const response = NextResponse.next();
  
  // Add tenant ID to headers for API calls
  if (tenantId) {
    response.headers.set('x-tenant-id', tenantId);
    response.cookies.set('tenant_id', tenantId, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30, // 30 days
    });
  }
  
  // Redirect to tenant selection if no tenant found and not on public pages
  const publicPaths = ['/', '/auth', '/pricing', '/about', '/contact', '/admin'];
  const isPublicPath = publicPaths.some(path => url.pathname.startsWith(path));
  
  if (!tenantId && !isPublicPath) {
    url.pathname = '/select-tenant';
    return NextResponse.redirect(url);
  }
  
  return response;
}

// Check if user has access to tenant
export async function checkTenantAccess(
  tenantId: string,
  userId: string,
  token: string
): Promise<boolean> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/tenants/${tenantId}/access`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-User-ID': userId,
        },
      }
    );
    
    return response.ok;
  } catch (error) {
    console.error('Error checking tenant access:', error);
    return false;
  }
}

// Get tenant configuration
export async function getTenantConfig(tenantId: string): Promise<any> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/tenants/${tenantId}/config`,
      {
        headers: {
          'X-Tenant-ID': tenantId,
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch tenant config');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching tenant config:', error);
    return null;
  }
}

// Validate tenant subdomain
export function validateSubdomain(subdomain: string): boolean {
  // Subdomain rules:
  // - 3-63 characters
  // - Lowercase letters, numbers, and hyphens only
  // - Cannot start or end with hyphen
  // - Cannot contain consecutive hyphens
  const regex = /^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$/;
  return regex.test(subdomain);
}

// Generate unique subdomain from company name
export function generateSubdomain(companyName: string): string {
  return companyName
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .substring(0, 63);
}
