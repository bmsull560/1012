# Security Implementation - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Dependencies (2 minutes)

```bash
cd frontend
npm install
```

New packages:
- `dompurify` - HTML sanitization
- `isomorphic-dompurify` - Server-side DOMPurify
- `react-markdown` - Safe markdown rendering

### 2. Verify Installation (1 minute)

```bash
npm list dompurify
# Should show: dompurify@3.0.6
```

### 3. Build & Test (2 minutes)

```bash
npm run build
npm test -- __tests__/security/
```

---

## ✅ What's Fixed

| Issue | Status | Impact |
|-------|--------|--------|
| Tokens in localStorage | ✅ FIXED | XSS protection |
| XSS via dangerouslySetInnerHTML | ✅ FIXED | Script injection blocked |
| No CSRF protection | ✅ FIXED | CSRF attacks prevented |
| Missing CSP headers | ✅ FIXED | Multiple attack vectors blocked |

---

## 🔧 Key Changes

### Authentication
```typescript
// OLD (INSECURE)
localStorage.setItem('access_token', token);

// NEW (SECURE)
// Tokens automatically in HttpOnly cookies
// No code changes needed!
```

### HTML Rendering
```typescript
// OLD (INSECURE)
<div dangerouslySetInnerHTML={{ __html: content }} />

// NEW (SECURE)
import { sanitizeMarkdownToHTML } from '@/lib/sanitize';
<SafeHTML content={content} />
```

### API Calls
```typescript
// OLD
fetch('/api/endpoint', { method: 'POST' })

// NEW (automatic)
fetch('/api/endpoint', { 
  method: 'POST',
  credentials: 'include' // Auto-added
})
```

---

## 📋 Deployment Checklist

### Pre-Deploy
- [ ] `npm install` completed
- [ ] `npm run build` successful
- [ ] Tests passing
- [ ] Environment variables set

### Deploy
```bash
npm run build
npm start
```

### Post-Deploy
- [ ] Check headers: `curl -I https://your-domain.com`
- [ ] Test login (tokens in cookies)
- [ ] Try XSS: `<script>alert('test')</script>` (should be sanitized)
- [ ] Monitor logs for errors

---

## 🧪 Quick Tests

### Test 1: Check Security Headers
```bash
curl -I https://your-domain.com | grep -i "content-security-policy\|strict-transport"
```

Expected:
```
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; ...
```

### Test 2: Verify Cookies
1. Open browser DevTools
2. Go to Application → Cookies
3. Look for `access_token` with:
   - ✅ HttpOnly flag
   - ✅ Secure flag
   - ✅ SameSite=Strict

### Test 3: Test XSS Protection
1. Open chat interface
2. Enter: `<script>alert('XSS')</script>`
3. Should display as text, not execute

### Test 4: Test CSRF Protection
```bash
# Should fail without CSRF token
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}'

# Expected: 403 Forbidden
```

---

## 🐛 Common Issues

### Issue: Build fails
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Issue: Users can't log in
```bash
# Solution: Clear old tokens
localStorage.clear();
# Then refresh and try again
```

### Issue: CSP blocking resources
```bash
# Check browser console for violations
# Update next.config.js CSP if needed
```

---

## 📚 Documentation

- **Full Guide:** `WEEK1_SECURITY_IMPLEMENTATION.md`
- **Summary:** `SECURITY_WEEK1_COMPLETE.md`
- **Frontend Audit:** `FRONTEND_SECURITY_ASSESSMENT.md`
- **Backend Audit:** `SECURITY_RISK_ANALYSIS.md`

---

## 🆘 Need Help?

### Quick Fixes

**Clear everything and start fresh:**
```bash
# Clear browser data
localStorage.clear();
document.cookie.split(";").forEach(c => {
  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
});

# Reinstall
rm -rf node_modules
npm install
npm run build
```

### Get Support

1. Check browser console for errors
2. Review `WEEK1_SECURITY_IMPLEMENTATION.md`
3. Run tests: `npm test -- __tests__/security/`
4. Contact security team for critical issues

---

## ✨ Success!

If all tests pass and headers are present, you're done! 🎉

**Security Status:** ✅ SECURE  
**Critical Issues:** 0  
**Ready for Production:** YES

---

**Last Updated:** 2025-10-26  
**Version:** 1.0.0
