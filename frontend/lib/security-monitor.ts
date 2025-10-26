/**
 * Security Monitoring and Alerting
 * Detects and reports security events
 */

import { logger } from './logger';

export type SecurityEventType =
  | 'xss_attempt'
  | 'csrf_failure'
  | 'auth_failure'
  | 'token_theft_attempt'
  | 'rate_limit_exceeded'
  | 'suspicious_activity'
  | 'csp_violation'
  | 'unauthorized_access';

export interface SecurityEvent {
  type: SecurityEventType;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details?: any;
  timestamp: string;
  userId?: string;
  sessionId?: string;
  ipAddress?: string;
  userAgent?: string;
}

export interface SecurityMonitorConfig {
  enableAlerts?: boolean;
  alertEndpoint?: string;
  enableCSPReporting?: boolean;
  cspReportEndpoint?: string;
  rateLimitWindow?: number; // milliseconds
  rateLimitThreshold?: number;
}

export class SecurityMonitor {
  private config: Required<SecurityMonitorConfig>;
  private eventCounts: Map<string, number[]> = new Map();

  constructor(config: SecurityMonitorConfig = {}) {
    this.config = {
      enableAlerts: config.enableAlerts ?? true,
      alertEndpoint: config.alertEndpoint || '/api/security/alert',
      enableCSPReporting: config.enableCSPReporting ?? true,
      cspReportEndpoint: config.cspReportEndpoint || '/api/security/csp-report',
      rateLimitWindow: config.rateLimitWindow || 60000, // 1 minute
      rateLimitThreshold: config.rateLimitThreshold || 10,
    };

    this.setupCSPReporting();
    this.setupGlobalErrorHandler();
  }

  /**
   * Report security event
   */
  async reportEvent(event: Omit<SecurityEvent, 'timestamp'>): Promise<void> {
    const fullEvent: SecurityEvent = {
      ...event,
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
    };

    // Log event
    logger.error(`Security Event: ${event.type}`, fullEvent);

    // Check if this is a rate limit violation
    if (this.isRateLimitExceeded(event.type)) {
      logger.warn('Rate limit exceeded for security events', { type: event.type });
      return;
    }

    // Send alert if enabled
    if (this.config.enableAlerts) {
      await this.sendAlert(fullEvent);
    }

    // Take automatic action based on severity
    this.handleSecurityEvent(fullEvent);
  }

  /**
   * Setup CSP violation reporting
   */
  private setupCSPReporting(): void {
    if (!this.config.enableCSPReporting || typeof document === 'undefined') {
      return;
    }

    document.addEventListener('securitypolicyviolation', (e) => {
      this.reportEvent({
        type: 'csp_violation',
        severity: 'high',
        message: 'Content Security Policy violation detected',
        details: {
          violatedDirective: e.violatedDirective,
          blockedURI: e.blockedURI,
          documentURI: e.documentURI,
          effectiveDirective: e.effectiveDirective,
          originalPolicy: e.originalPolicy,
          sourceFile: e.sourceFile,
          lineNumber: e.lineNumber,
          columnNumber: e.columnNumber,
        },
      });
    });
  }

  /**
   * Setup global error handler
   */
  private setupGlobalErrorHandler(): void {
    if (typeof window === 'undefined') {
      return;
    }

    window.addEventListener('error', (event) => {
      // Check for potential security issues in errors
      const errorMessage = event.message?.toLowerCase() || '';
      
      if (errorMessage.includes('script') || errorMessage.includes('eval')) {
        this.reportEvent({
          type: 'xss_attempt',
          severity: 'critical',
          message: 'Potential XSS attempt detected in error',
          details: {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
          },
        });
      }
    });

    window.addEventListener('unhandledrejection', (event) => {
      // Check for auth-related promise rejections
      const reason = event.reason?.toString().toLowerCase() || '';
      
      if (reason.includes('unauthorized') || reason.includes('401')) {
        this.reportEvent({
          type: 'auth_failure',
          severity: 'medium',
          message: 'Authentication failure detected',
          details: {
            reason: event.reason,
          },
        });
      }
    });
  }

  /**
   * Check if rate limit is exceeded
   */
  private isRateLimitExceeded(eventType: string): boolean {
    const now = Date.now();
    const windowStart = now - this.config.rateLimitWindow;

    // Get or create event timestamps array
    if (!this.eventCounts.has(eventType)) {
      this.eventCounts.set(eventType, []);
    }

    const timestamps = this.eventCounts.get(eventType)!;

    // Remove old timestamps
    const recentTimestamps = timestamps.filter(ts => ts > windowStart);
    this.eventCounts.set(eventType, recentTimestamps);

    // Add current timestamp
    recentTimestamps.push(now);

    // Check if threshold exceeded
    return recentTimestamps.length > this.config.rateLimitThreshold;
  }

  /**
   * Send alert to backend
   */
  private async sendAlert(event: SecurityEvent): Promise<void> {
    try {
      await fetch(this.config.alertEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
        credentials: 'include',
      });
    } catch (error) {
      logger.error('Failed to send security alert', { error });
    }
  }

  /**
   * Handle security event with automatic actions
   */
  private handleSecurityEvent(event: SecurityEvent): void {
    switch (event.severity) {
      case 'critical':
        // Critical events - take immediate action
        if (event.type === 'xss_attempt' || event.type === 'token_theft_attempt') {
          // Log out user immediately
          this.emergencyLogout();
        }
        break;

      case 'high':
        // High severity - warn user
        if (typeof window !== 'undefined') {
          console.warn('Security Warning:', event.message);
        }
        break;

      case 'medium':
      case 'low':
        // Log only
        break;
    }
  }

  /**
   * Emergency logout on critical security event
   */
  private emergencyLogout(): void {
    if (typeof window !== 'undefined') {
      // Clear any client-side data
      sessionStorage.clear();
      
      // Redirect to login
      window.location.href = '/login?reason=security';
    }
  }

  /**
   * Monitor for suspicious patterns
   */
  detectSuspiciousActivity(): void {
    if (typeof window === 'undefined') {
      return;
    }

    // Monitor for rapid page navigation (potential bot)
    let navigationCount = 0;
    const navigationWindow = 5000; // 5 seconds

    const originalPushState = history.pushState;
    history.pushState = function(...args) {
      navigationCount++;
      
      setTimeout(() => {
        navigationCount--;
      }, navigationWindow);

      if (navigationCount > 10) {
        securityMonitor.reportEvent({
          type: 'suspicious_activity',
          severity: 'medium',
          message: 'Rapid page navigation detected',
          details: { navigationCount },
        });
      }

      return originalPushState.apply(history, args);
    };

    // Monitor for console access (potential debugging/tampering)
    const devtools = /./;
    devtools.toString = function() {
      securityMonitor.reportEvent({
        type: 'suspicious_activity',
        severity: 'low',
        message: 'Developer tools opened',
      });
      return 'devtools';
    };
    console.log('%c', devtools);

    // Monitor for localStorage access attempts
    const originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = function(key: string, value: string) {
      if (key.includes('token') || key.includes('password')) {
        securityMonitor.reportEvent({
          type: 'token_theft_attempt',
          severity: 'critical',
          message: 'Attempt to store sensitive data in localStorage',
          details: { key },
        });
      }
      return originalSetItem.call(this, key, value);
    };
  }
}

// Global security monitor instance
let securityMonitor: SecurityMonitor;

/**
 * Initialize security monitor
 */
export function initSecurityMonitor(config?: SecurityMonitorConfig): SecurityMonitor {
  if (!securityMonitor) {
    securityMonitor = new SecurityMonitor(config);
    securityMonitor.detectSuspiciousActivity();
  }
  return securityMonitor;
}

/**
 * Get security monitor instance
 */
export function getSecurityMonitor(): SecurityMonitor {
  if (!securityMonitor) {
    securityMonitor = new SecurityMonitor();
  }
  return securityMonitor;
}

/**
 * Report security event (convenience function)
 */
export function reportSecurityEvent(
  type: SecurityEventType,
  severity: 'low' | 'medium' | 'high' | 'critical',
  message: string,
  details?: any
): void {
  getSecurityMonitor().reportEvent({ type, severity, message, details });
}

// Export singleton
export { securityMonitor };
