/**
 * Secure Logging Service
 * Sanitizes sensitive data before logging
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  level: LogLevel;
  message: string;
  data?: any;
  timestamp: string;
  context?: string;
  userId?: string;
  sessionId?: string;
}

export interface LoggerConfig {
  level?: LogLevel;
  enableConsole?: boolean;
  enableRemote?: boolean;
  remoteEndpoint?: string;
  sanitize?: boolean;
  context?: string;
}

/**
 * Sensitive field patterns to redact
 */
const SENSITIVE_PATTERNS = {
  // Authentication
  password: /password/i,
  token: /token|jwt|bearer/i,
  secret: /secret|key|api[_-]?key/i,
  auth: /authorization|auth[_-]?header/i,
  
  // Personal Information
  email: /email/i,
  phone: /phone|mobile|tel/i,
  ssn: /ssn|social[_-]?security/i,
  
  // Financial
  card: /card[_-]?number|credit[_-]?card|cvv|cvc/i,
  account: /account[_-]?number|bank[_-]?account/i,
  
  // Session
  session: /session[_-]?id|session[_-]?token/i,
  cookie: /cookie/i,
};

/**
 * Secure Logger Class
 */
export class SecureLogger {
  private config: Required<LoggerConfig>;
  private logBuffer: LogEntry[] = [];
  private flushTimer: NodeJS.Timeout | null = null;

  constructor(config: LoggerConfig = {}) {
    this.config = {
      level: config.level || (process.env.NODE_ENV === 'production' ? 'warn' : 'debug'),
      enableConsole: config.enableConsole ?? (process.env.NODE_ENV !== 'production'),
      enableRemote: config.enableRemote ?? (process.env.NODE_ENV === 'production'),
      remoteEndpoint: config.remoteEndpoint || '/api/logs',
      sanitize: config.sanitize ?? true,
      context: config.context || 'app',
    };
  }

  /**
   * Log debug message
   */
  debug(message: string, data?: any): void {
    this.log('debug', message, data);
  }

  /**
   * Log info message
   */
  info(message: string, data?: any): void {
    this.log('info', message, data);
  }

  /**
   * Log warning message
   */
  warn(message: string, data?: any): void {
    this.log('warn', message, data);
  }

  /**
   * Log error message
   */
  error(message: string, data?: any): void {
    this.log('error', message, data);
  }

  /**
   * Main logging method
   */
  private log(level: LogLevel, message: string, data?: any): void {
    // Check if level is enabled
    if (!this.shouldLog(level)) {
      return;
    }

    // Sanitize data if enabled
    const sanitizedData = this.config.sanitize ? this.sanitizeData(data) : data;

    // Create log entry
    const entry: LogEntry = {
      level,
      message,
      data: sanitizedData,
      timestamp: new Date().toISOString(),
      context: this.config.context,
    };

    // Console logging
    if (this.config.enableConsole) {
      this.logToConsole(entry);
    }

    // Remote logging
    if (this.config.enableRemote) {
      this.logToRemote(entry);
    }
  }

  /**
   * Check if log level should be logged
   */
  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    const configLevelIndex = levels.indexOf(this.config.level);
    const messageLevelIndex = levels.indexOf(level);
    
    return messageLevelIndex >= configLevelIndex;
  }

  /**
   * Sanitize sensitive data
   */
  private sanitizeData(data: any): any {
    if (data === null || data === undefined) {
      return data;
    }

    // Handle Error objects
    if (data instanceof Error) {
      return {
        name: data.name,
        message: data.message,
        stack: process.env.NODE_ENV === 'production' ? undefined : data.stack,
      };
    }

    // Handle strings
    if (typeof data === 'string') {
      return this.sanitizeString(data);
    }

    // Handle arrays
    if (Array.isArray(data)) {
      return data.map(item => this.sanitizeData(item));
    }

    // Handle objects
    if (typeof data === 'object') {
      const sanitized: any = {};
      
      for (const [key, value] of Object.entries(data)) {
        // Check if key matches sensitive pattern
        if (this.isSensitiveKey(key)) {
          sanitized[key] = '[REDACTED]';
        } else {
          sanitized[key] = this.sanitizeData(value);
        }
      }
      
      return sanitized;
    }

    return data;
  }

  /**
   * Check if key is sensitive
   */
  private isSensitiveKey(key: string): boolean {
    return Object.values(SENSITIVE_PATTERNS).some(pattern => pattern.test(key));
  }

  /**
   * Sanitize string (remove tokens, etc.)
   */
  private sanitizeString(str: string): string {
    // Remove JWT tokens
    str = str.replace(/Bearer\s+[\w-]+\.[\w-]+\.[\w-]+/gi, 'Bearer [REDACTED]');
    
    // Remove API keys
    str = str.replace(/api[_-]?key[:\s=]+[\w-]+/gi, 'api_key=[REDACTED]');
    
    // Remove email addresses (partial)
    str = str.replace(/([a-zA-Z0-9._-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, 
      (match, user, domain) => `${user.substring(0, 2)}***@${domain}`
    );
    
    return str;
  }

  /**
   * Log to console
   */
  private logToConsole(entry: LogEntry): void {
    const prefix = `[${entry.timestamp}] [${entry.level.toUpperCase()}] [${entry.context}]`;
    
    switch (entry.level) {
      case 'debug':
        console.debug(prefix, entry.message, entry.data);
        break;
      case 'info':
        console.info(prefix, entry.message, entry.data);
        break;
      case 'warn':
        console.warn(prefix, entry.message, entry.data);
        break;
      case 'error':
        console.error(prefix, entry.message, entry.data);
        break;
    }
  }

  /**
   * Log to remote service
   */
  private logToRemote(entry: LogEntry): void {
    // Add to buffer
    this.logBuffer.push(entry);

    // Flush buffer if it's too large or after a delay
    if (this.logBuffer.length >= 10) {
      this.flushLogs();
    } else if (!this.flushTimer) {
      this.flushTimer = setTimeout(() => {
        this.flushLogs();
      }, 5000); // Flush after 5 seconds
    }
  }

  /**
   * Flush logs to remote service
   */
  private async flushLogs(): Promise<void> {
    if (this.logBuffer.length === 0) {
      return;
    }

    // Clear timer
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }

    // Get logs to send
    const logsToSend = [...this.logBuffer];
    this.logBuffer = [];

    try {
      await fetch(this.config.remoteEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: logsToSend }),
        credentials: 'include',
      });
    } catch (error) {
      // Failed to send logs, add back to buffer
      this.logBuffer.unshift(...logsToSend);
      
      // Log to console as fallback
      if (this.config.enableConsole) {
        console.error('Failed to send logs to remote service:', error);
      }
    }
  }

  /**
   * Create child logger with additional context
   */
  child(context: string): SecureLogger {
    return new SecureLogger({
      ...this.config,
      context: `${this.config.context}:${context}`,
    });
  }
}

// Global logger instance
let globalLogger: SecureLogger | null = null;

/**
 * Get or create global logger
 */
export function getLogger(config?: LoggerConfig): SecureLogger {
  if (!globalLogger) {
    globalLogger = new SecureLogger(config);
  }
  return globalLogger;
}

/**
 * Create a new logger instance
 */
export function createLogger(config?: LoggerConfig): SecureLogger {
  return new SecureLogger(config);
}

// Export convenience functions
export const logger = {
  debug: (message: string, data?: any) => getLogger().debug(message, data),
  info: (message: string, data?: any) => getLogger().info(message, data),
  warn: (message: string, data?: any) => getLogger().warn(message, data),
  error: (message: string, data?: any) => getLogger().error(message, data),
  child: (context: string) => getLogger().child(context),
};
