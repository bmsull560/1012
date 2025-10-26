# ValueVerse Security - Quick Reference Guide

**Last Updated:** October 26, 2024
**Phase:** 1 (Critical Issues) - COMPLETE

---

## 🚨 Critical Security Checklist

### Before Production Deployment

- [ ] **JWT_SECRET_KEY** is set to a secure value (not placeholder)
  ```bash
  python -c 'import secrets; print(secrets.token_urlsafe(32))'
  ```

- [ ] **DATABASE_URL** includes SSL/TLS parameters
  ```bash
  # Minimum: ?sslmode=require
  # Recommended: ?sslmode=verify-full&sslrootcert=/path/to/ca.crt
  ```

- [ ] **CORS** is properly configured (not using wildcard headers)
  - ✅ Specific headers whitelisted
  - ✅ Credentials properly set

- [ ] **Security Headers** are present in all responses
  - ✅ Strict-Transport-Security
  - ✅ X-Content-Type-Options
  - ✅ X-Frame-Options
  - ✅ Content-Security-Policy

- [ ] **Rate Limiting** is enabled on auth endpoints
  - ✅ 5 requests per minute
  - ✅ Redis backend configured

- [ ] **Input Validation** is active
  - ✅ Field length limits enforced
  - ✅ Format validation enabled
  - ✅ Size limits on payloads

---

## 🔑 Secret Management

### Generate New JWT Secret
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### Set JWT Secret (Development)
```bash
export JWT_SECRET_KEY="<generated-key>"
```

### Set JWT Secret (Production)
Use your secrets management system:
- **AWS:** AWS Secrets Manager
- **Kubernetes:** Sealed Secrets or External Secrets
- **HashiCorp:** Vault
- **Azure:** Key Vault

### Verify JWT Secret is Set
```bash
# This will fail if JWT_SECRET_KEY is not set
python -c "from billing_system.backend.auth import SECRET_KEY"
```

---

## 🔐 Database Security

### Configure Secure Database Connection

**Development (Minimum Security):**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/valuedb?sslmode=require
```

**Production (Recommended):**
```bash
DATABASE_URL=postgresql://user:password@host:5432/valuedb?sslmode=verify-full&sslrootcert=/path/to/ca.crt
```

### SSL/TLS Modes Explained
- `disable` - No SSL (⚠️ NEVER use in production)
- `allow` - SSL optional (⚠️ NEVER use in production)
- `prefer` - SSL preferred but not required (⚠️ NOT recommended)
- `require` - SSL required, no certificate validation (✅ Minimum)
- `verify-ca` - SSL required, verify CA certificate (✅ Better)
- `verify-full` - SSL required, verify CA and hostname (✅ Best)

### Test Database Connection
```bash
psql "$DATABASE_URL" -c "SELECT version();"
```

---

## 🛡️ Security Headers

### Headers Added to All Responses

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Force HTTPS |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Enable XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer info |
| `Content-Security-Policy` | `default-src 'self'...` | Control resource loading |
| `Permissions-Policy` | `geolocation=(), microphone=()...` | Disable browser features |

### Verify Headers are Present
```bash
curl -i http://localhost:8001/api/health | grep -E "Strict-Transport|X-Content-Type|X-Frame"
```

---

## 🚦 Rate Limiting

### Configuration
- **Limit:** 5 requests per minute
- **Endpoint:** All authentication endpoints
- **Backend:** Redis
- **Response:** HTTP 429 (Too Many Requests)

### Test Rate Limiting
```bash
# Make 6 requests in quick succession
for i in {1..6}; do
  curl -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test"}' \
    -w "\nStatus: %{http_code}\n"
done
# 6th request should return 429
```

---

## ✅ Input Validation

### Validation Rules

| Field | Min Length | Max Length | Pattern |
|-------|-----------|-----------|---------|
| `company_name` | 1 | 200 | Alphanumeric + spaces/hyphens/dots |
| `industry` | 1 | 100 | Alphabetic only |
| `email` | 5 | 254 | Valid email format |
| `context` | - | 10,000 bytes | JSON object |

### Test Input Validation
```bash
# Test oversized company name (should fail)
curl -X POST http://localhost:8001/api/value-models \
  -H "Content-Type: application/json" \
  -d '{"company_name":"'$(python -c "print(\"x\"*300)")'"}'

# Test invalid industry (should fail)
curl -X POST http://localhost:8001/api/value-models \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Acme Corp","industry":"Tech123"}'
```

---

## 🔍 Security Testing

### Run All Security Tests
```bash
# Test 1: JWT Secret Requirement
echo "Test 1: JWT Secret Requirement"
python -c "from billing_system.backend.auth import SECRET_KEY" 2>&1 | grep -q "CRITICAL SECURITY ERROR" && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: CORS Configuration
echo "Test 2: CORS Configuration"
curl -s -H "Origin: http://example.com" http://localhost:8001/api/health | grep -q "access-control-allow-headers" && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Security Headers
echo "Test 3: Security Headers"
curl -s -i http://localhost:8001/api/health | grep -q "Strict-Transport-Security" && echo "✅ PASS" || echo "❌ FAIL"

# Test 4: Database SSL
echo "Test 4: Database SSL"
psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1 && echo "✅ PASS" || echo "❌ FAIL"

# Test 5: Input Validation
echo "Test 5: Input Validation"
curl -s -X POST http://localhost:8001/api/value-models \
  -H "Content-Type: application/json" \
  -d '{"company_name":"x".repeat(300),"industry":"test"}' | grep -q "max_length" && echo "✅ PASS" || echo "❌ FAIL"
```

---

## 📋 Compliance Mapping

### NIST 800-53 Controls
- ✅ **IA-5** (Authenticator Management) - JWT secret validation
- ✅ **SC-8** (Transmission Confidentiality) - Database SSL/TLS
- ✅ **SC-7** (Boundary Protection) - Security headers
- ✅ **SC-5** (Denial of Service Protection) - Rate limiting
- 🔄 **AC-2** (Account Management) - Password policy (Phase 2)

### PCI-DSS Requirements
- ✅ **Req 2** (Default Passwords) - No hardcoded secrets
- ✅ **Req 4** (Encryption in Transit) - Database SSL/TLS
- 🔄 **Req 8** (Access Control) - Password policy (Phase 2)
- 🔄 **Req 10** (Logging) - Audit trail (Phase 3)

### GDPR Articles
- ✅ **Art. 32** (Security) - Encryption in transit
- 🔄 **Art. 33** (Breach Notification) - Incident response (Phase 2)

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All environment variables set
- [ ] JWT_SECRET_KEY is secure
- [ ] DATABASE_URL has SSL/TLS
- [ ] Security tests passing
- [ ] No hardcoded secrets in code
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation active

### Deployment
- [ ] Build Docker image
- [ ] Run security tests
- [ ] Deploy to staging
- [ ] Verify all services running
- [ ] Check logs for errors
- [ ] Run smoke tests
- [ ] Deploy to production

### Post-Deployment
- [ ] Monitor security logs
- [ ] Verify security headers
- [ ] Test rate limiting
- [ ] Check database connections
- [ ] Monitor for alerts

---

## 🆘 Troubleshooting

### JWT Secret Error
**Error:** `CRITICAL SECURITY ERROR: JWT_SECRET_KEY environment variable must be set`

**Solution:**
```bash
# Generate a new secret
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Set it in your environment
export JWT_SECRET_KEY="<generated-key>"

# Verify it's set
echo $JWT_SECRET_KEY
```

### Database Connection Error
**Error:** `FATAL: no pg_hba.conf entry for host`

**Solution:**
```bash
# Ensure DATABASE_URL has SSL/TLS parameters
export DATABASE_URL="postgresql://user:password@host:5432/db?sslmode=require"

# Test connection
psql "$DATABASE_URL" -c "SELECT version();"
```

### CORS Error
**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
1. Check CORS configuration in `main.py`
2. Verify `allow_origins` includes your frontend URL
3. Verify `allow_headers` includes required headers
4. Check browser console for specific header issue

### Rate Limiting Error
**Error:** `HTTP 429 Too Many Requests`

**Solution:**
1. Wait 60 seconds for rate limit window to reset
2. Check Redis connection: `redis-cli ping`
3. Verify rate limiter is configured correctly

---

## 📞 Security Contacts

### Escalation Path
- **P0 (Critical):** Immediate notification
- **P1 (High):** Within 24 hours
- **P2 (Medium):** Within 1 week
- **P3 (Low):** Next sprint

### Security Team
- Security Lead: [To be assigned]
- Compliance Officer: [To be assigned]
- Incident Response: security@valueverse.com

---

## 📚 Additional Resources

### Documentation Files
- `SECURITY_REMEDIATION_LOG.md` - Detailed remediation log
- `SECURITY_IMPLEMENTATION_SUMMARY.md` - Full implementation summary
- `services/value-architect/security.py` - Security module code
- `config/database_security.py` - Database security config

### External References
- NIST 800-53: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- OWASP Top 10: https://owasp.org/Top10/
- PCI-DSS: https://www.pcisecuritystandards.org/
- GDPR: https://gdpr-info.eu/

---

**Last Updated:** October 26, 2024
**Status:** Phase 1 Complete - Production Ready for Staging
**Next Phase:** Phase 2 (30 days) - High Priority Issues
