# Frontend Security Implementation Guide

**Priority:** CRITICAL  
**Timeline:** Week 1 (All critical issues)  
**Status:** Ready for implementation

---

## 🚨 Fix 1: Move Tokens from localStorage to HttpOnly Cookies

### Current Issue
**File:** `frontend/services/api.ts:16-18`  
**Risk:** XSS attacks can steal tokens from localStorage

### Implementation

#### Step 1: Update API Service
```typescript
// frontend/services/api.ts

class ApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  // Remove all localStorage references
  private getAuthHeaders(): HeadersInit {
    // No longer needed - cookies sent automatically
    return {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest', // CSRF protection
    };
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
      credentials: 'include', // CRITICAL: Include cookies in requests
    });

    if (response.status === 401) {
      // Try to refresh token
      await this.refreshToken();
      // Retry request
      return this.request(endpoint, options);
    }

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async refreshToken(): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      // Redirect to login
      window.location.href = '/login';
    }
  }
}

export const apiService = new ApiService();
```

#### Step 2: Update Auth Context
```typescript
// frontend/contexts/AuthContext.tsx

import { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '@/services/api';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const userData = await apiService.request<User>('/api/auth/me');
      setUser(userData);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiService.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    // Cookies are set by backend automatically
    setUser(response.user);
  };

  const logout = async () => {
    await apiService.request('/api/auth/logout', {
      method: 'POST',
    });
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
```

---

## 🚨 Fix 2: Sanitize dangerouslySetInnerHTML

### Current Issue
**File:** `frontend/components/agents/StructuredAgentChat.tsx:565`  
**Risk:** XSS via unsanitized HTML content

### Implementation

#### Step 1: Install DOMPurify
```bash
npm install dompurify @types/dompurify
```

#### Step 2: Create Sanitization Hook
```typescript
// frontend/hooks/useSanitizedHTML.ts

import DOMPurify from 'dompurify';
import { useMemo } from 'react';

interface SanitizeOptions {
  allowedTags?: string[];
  allowedAttributes?: string[];
  allowImages?: boolean;
  allowLinks?: boolean;
}

export function useSanitizedHTML(
  dirty: string,
  options: SanitizeOptions = {}
): string {
  return useMemo(() => {
    // Configure DOMPurify
    const config: DOMPurify.Config = {
      ALLOWED_TAGS: options.allowedTags || [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 
        'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 
        'code', 'pre', 'span', 'div'
      ],
      ALLOWED_ATTR: options.allowedAttributes || ['class', 'id'],
      ALLOW_DATA_ATTR: false,
      ALLOW_UNKNOWN_PROTOCOLS: false,
    };

    if (options.allowImages) {
      config.ALLOWED_TAGS!.push('img');
      config.ALLOWED_ATTR!.push('src', 'alt');
    }

    if (options.allowLinks) {
      config.ALLOWED_TAGS!.push('a');
      config.ALLOWED_ATTR!.push('href', 'target');
      // Only allow safe protocols
      config.ALLOWED_URI_REGEXP = /^(?:(?:https?|mailto):|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i;
    }

    return DOMPurify.sanitize(dirty, config);
  }, [dirty, options]);
}
```

#### Step 3: Update Component
```typescript
// frontend/components/agents/StructuredAgentChat.tsx

import { useSanitizedHTML } from '@/hooks/useSanitizedHTML';

const StructuredAgentChat: React.FC = () => {
  // ... existing code ...

  const renderMessage = (message: Message) => {
    // Sanitize HTML content
    const sanitizedContent = useSanitizedHTML(message.content, {
      allowLinks: true,
      allowImages: false, // Don't allow images in chat
    });

    return (
      <div className="message">
        {/* Safe: content is sanitized */}
        <div dangerouslySetInnerHTML={{ __html: sanitizedContent }} />
      </div>
    );
  };

  // Alternative: Use markdown parser instead
  const renderMarkdown = (content: string) => {
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Customize rendering to prevent XSS
          a: ({ href, children }) => {
            const isExternal = href?.startsWith('http');
            return (
              <a 
                href={href}
                target={isExternal ? '_blank' : undefined}
                rel={isExternal ? 'noopener noreferrer' : undefined}
              >
                {children}
              </a>
            );
          },
          img: () => null, // Disable images
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };
};
```

---

## 🚨 Fix 3: Implement CSRF Protection

### Implementation

#### Step 1: Add CSRF Token Management
```typescript
// frontend/services/csrf.ts

class CSRFService {
  private token: string | null = null;

  async getToken(): Promise<string> {
    if (!this.token) {
      await this.fetchToken();
    }
    return this.token!;
  }

  private async fetchToken(): Promise<void> {
    const response = await fetch('/api/csrf-token', {
      credentials: 'include',
    });
    const data = await response.json();
    this.token = data.csrfToken;
  }

  getHeaders(): HeadersInit {
    return {
      'X-CSRF-Token': this.token || '',
    };
  }
}

export const csrfService = new CSRFService();
```

#### Step 2: Update API Service with CSRF
```typescript
// frontend/services/api.ts

import { csrfService } from './csrf';

class ApiService {
  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Get CSRF token for state-changing requests
    const needsCSRF = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(
      options.method || 'GET'
    );

    let headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (needsCSRF) {
      const csrfToken = await csrfService.getToken();
      headers = {
        ...headers,
        'X-CSRF-Token': csrfToken,
      };
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });

    // Handle CSRF token refresh
    if (response.status === 403 && response.headers.get('X-CSRF-Error')) {
      await csrfService.fetchToken();
      return this.request(endpoint, options); // Retry
    }

    return response.json();
  }
}
```

#### Step 3: Add Double Submit Cookie Pattern
```typescript
// frontend/middleware.ts

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { v4 as uuidv4 } from 'uuid';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();
  
  // Set CSRF token cookie if not present
  if (!request.cookies.get('csrf-token')) {
    const token = uuidv4();
    response.cookies.set('csrf-token', token, {
      httpOnly: false, // Needs to be readable by JS
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      path: '/',
    });
  }

  // Add security headers
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  return response;
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
```

---

## 🛡️ Fix 4: Add Content Security Policy

### Implementation in next.config.js
```javascript
// frontend/next.config.js

const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://cdn.jsdelivr.net",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self' data:",
      "connect-src 'self' wss: https:",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests",
    ].join('; '),
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=31536000; includeSubDomains; preload',
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()',
  },
];

module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders,
      },
    ];
  },
  
  // Additional security configurations
  poweredByHeader: false,
  
  // Environment-specific settings
  env: {
    // Don't expose sensitive vars to client
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    // NOT: DATABASE_URL, JWT_SECRET, etc.
  },
};
```

---

## 🔒 Fix 5: Secure WebSocket Connection

### Implementation
```typescript
// frontend/services/websocket.ts

class SecureWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(): void {
    // Force WSS in production
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    // Don't send token in URL
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = async () => {
      // Authenticate after connection
      await this.authenticate();
      this.reconnectAttempts = 0;
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.reconnect();
    };

    this.ws.onclose = () => {
      this.reconnect();
    };
  }

  private async authenticate(): Promise<void> {
    // Send auth message after connection established
    // Server validates session cookie
    this.send({
      type: 'auth',
      timestamp: Date.now(),
    });
  }

  private reconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
    }
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  close(): void {
    this.ws?.close();
  }
}

export const wsService = new SecureWebSocketService();
```

---

## 🚫 Fix 6: Remove Sensitive Logging

### Implementation
```typescript
// frontend/utils/logger.ts

const isDevelopment = process.env.NODE_ENV === 'development';

class Logger {
  private sensitivePatterns = [
    /password/i,
    /token/i,
    /secret/i,
    /api[_-]?key/i,
    /authorization/i,
    /cookie/i,
    /session/i,
  ];

  private sanitize(data: any): any {
    if (typeof data === 'string') {
      return data;
    }

    if (typeof data === 'object' && data !== null) {
      const sanitized: any = Array.isArray(data) ? [] : {};
      
      for (const key in data) {
        // Check if key contains sensitive pattern
        const isSensitive = this.sensitivePatterns.some(
          pattern => pattern.test(key)
        );

        if (isSensitive) {
          sanitized[key] = '[REDACTED]';
        } else {
          sanitized[key] = this.sanitize(data[key]);
        }
      }
      
      return sanitized;
    }

    return data;
  }

  log(...args: any[]): void {
    if (isDevelopment) {
      console.log(...args.map(arg => this.sanitize(arg)));
    }
  }

  error(...args: any[]): void {
    // Always log errors, but sanitize in production
    const sanitizedArgs = isDevelopment 
      ? args 
      : args.map(arg => this.sanitize(arg));
    
    console.error(...sanitizedArgs);
    
    // Send to error tracking service
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.captureException(new Error(sanitizedArgs.join(' ')));
    }
  }

  warn(...args: any[]): void {
    if (isDevelopment) {
      console.warn(...args.map(arg => this.sanitize(arg)));
    }
  }
}

export const logger = new Logger();
```

---

## ✅ Testing Checklist

### Security Tests
```typescript
// frontend/__tests__/security.test.ts

describe('Security Tests', () => {
  it('should not store tokens in localStorage', () => {
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('refreshToken')).toBeNull();
  });

  it('should include credentials in API requests', async () => {
    const fetchSpy = jest.spyOn(global, 'fetch');
    await apiService.request('/api/test');
    
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        credentials: 'include',
      })
    );
  });

  it('should sanitize HTML content', () => {
    const dirty = '<script>alert("XSS")</script><p>Safe content</p>';
    const clean = DOMPurify.sanitize(dirty);
    
    expect(clean).not.toContain('<script>');
    expect(clean).toContain('<p>Safe content</p>');
  });

  it('should include CSRF token in mutations', async () => {
    const fetchSpy = jest.spyOn(global, 'fetch');
    await apiService.request('/api/update', { method: 'POST' });
    
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-CSRF-Token': expect.any(String),
        }),
      })
    );
  });
});
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Remove all localStorage token references
- [ ] Install DOMPurify
- [ ] Add CSP headers to next.config.js
- [ ] Implement CSRF protection
- [ ] Remove console.log statements
- [ ] Test in production mode locally

### Deployment
- [ ] Verify cookies are HttpOnly and Secure
- [ ] Check CSP headers are present
- [ ] Confirm WebSocket uses WSS
- [ ] Validate CSRF tokens working
- [ ] Monitor for XSS attempts

### Post-Deployment
- [ ] Run security scanner
- [ ] Check browser console for CSP violations
- [ ] Monitor error tracking for security issues
- [ ] Review authentication flows
- [ ] Test all forms for CSRF protection

---

## 🎯 Timeline

### Week 1 (Critical)
- Day 1-2: Move tokens to HttpOnly cookies
- Day 2-3: Fix XSS vulnerabilities
- Day 3-4: Implement CSRF protection
- Day 4-5: Add CSP headers and test

### Week 2 (High Priority)
- Secure WebSocket connections
- Remove sensitive logging
- Implement token refresh
- Add session timeout

---

**Status:** Ready for implementation  
**Priority:** CRITICAL - Must complete before production  
**Estimated Effort:** 40 hours total
