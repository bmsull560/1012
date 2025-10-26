/**
 * Security Tests for Logging
 */

import { describe, it, expect } from '@jest/globals';
import { SecureLogger } from '@/lib/logger';

describe('Secure Logging', () => {
  describe('Data Sanitization', () => {
    it('should redact passwords', () => {
      const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
      
      const data = {
        username: 'test@example.com',
        password: 'secret123',
      };

      // Access private method for testing
      const sanitized = (logger as any).sanitizeData(data);
      
      expect(sanitized.password).toBe('[REDACTED]');
      expect(sanitized.username).not.toBe('[REDACTED]');
    });

    it('should redact tokens', () => {
      const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
      
      const data = {
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        refresh_token: 'refresh_token_value',
      };

      const sanitized = (logger as any).sanitizeData(data);
      
      expect(sanitized.access_token).toBe('[REDACTED]');
      expect(sanitized.refresh_token).toBe('[REDACTED]');
    });

    it('should redact API keys', () => {
      const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
      
      const data = {
        api_key: 'sk_live_1234567890',
        apiKey: 'pk_test_abcdefghij',
      };

      const sanitized = (logger as any).sanitizeData(data);
      
      expect(sanitized.api_key).toBe('[REDACTED]');
      expect(sanitized.apiKey).toBe('[REDACTED]');
    });

    it('should partially redact emails', () => {
      const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
      
      const message = 'User test@example.com logged in';
      const sanitized = (logger as any).sanitizeString(message);
      
      expect(sanitized).toContain('te***@example.com');
      expect(sanitized).not.toContain('test@example.com');
    });

    it('should redact Bearer tokens in strings', () => {
      const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
      
      const message = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.xxx';
      const sanitized = (logger as any).sanitizeString(message);
      
      expect(sanitized).toContain('Bearer [REDACTED]');
      expect(sanitized).not.toContain('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9');
    });

    it('should handle nested objects', () => {
      const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
      
      const data = {
        user: {
          email: 'test@example.com',
          password: 'secret',
        },
        auth: {
          token: 'jwt_token',
        },
      };

      const sanitized = (logger as any).sanitizeData(data);
      
      expect(sanitized.user.password).toBe('[REDACTED]');
      expect(sanitized.auth.token).toBe('[REDACTED]');
    });

    it('should handle arrays', () => {
      const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
      
      const data = [
        { password: 'secret1' },
        { password: 'secret2' },
      ];

      const sanitized = (logger as any).sanitizeData(data);
      
      expect(sanitized[0].password).toBe('[REDACTED]');
      expect(sanitized[1].password).toBe('[REDACTED]');
    });

    it('should handle Error objects', () => {
      const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
      
      const error = new Error('Test error');
      const sanitized = (logger as any).sanitizeData(error);
      
      expect(sanitized.name).toBe('Error');
      expect(sanitized.message).toBe('Test error');
    });
  });

  describe('Log Levels', () => {
    it('should respect log level configuration', () => {
      const logger = new SecureLogger({ 
        level: 'error',
        enableConsole: false,
        enableRemote: false,
      });

      // Debug and info should not log when level is error
      expect((logger as any).shouldLog('debug')).toBe(false);
      expect((logger as any).shouldLog('info')).toBe(false);
      expect((logger as any).shouldLog('warn')).toBe(false);
      expect((logger as any).shouldLog('error')).toBe(true);
    });
  });

  describe('Child Loggers', () => {
    it('should create child logger with additional context', () => {
      const parentLogger = new SecureLogger({ context: 'app' });
      const childLogger = parentLogger.child('auth');
      
      expect((childLogger as any).config.context).toBe('app:auth');
    });
  });
});

describe('Token Theft Prevention', () => {
  it('should not log tokens even if passed', () => {
    const logger = new SecureLogger({ enableConsole: false, enableRemote: false });
    
    const maliciousData = {
      message: 'Stealing token',
      stolen_token: localStorage.getItem('access_token'), // Would be null now
      access_token: 'fake_token',
    };

    const sanitized = (logger as any).sanitizeData(maliciousData);
    
    expect(sanitized.access_token).toBe('[REDACTED]');
  });
});
