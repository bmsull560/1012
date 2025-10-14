# Database Security & Performance Implementation Guide

## Overview
This guide covers the implementation of 4 critical database improvements:
1. **Row-Level Security (RLS)** - Tenant isolation at database level
2. **Encryption at Rest** - PCI compliance for sensitive data
3. **Critical Indexes** - Performance optimization for 1M+ events/min
4. **Audit Triggers** - Compliance and security monitoring

## Pre-Implementation Checklist

- [ ] **Backup database** before starting
- [ ] **Test in staging** environment first
- [ ] **Schedule maintenance window** (estimated 4-6 hours)
- [ ] **Notify stakeholders** of potential brief disruptions
- [ ] **Prepare rollback plan** in case of issues
- [ ] **Monitor application logs** during implementation

## Implementation Order & Timeline

### Day 1: Row-Level Security (3-4 hours)
**Risk Level: HIGH** | **Downtime: None** | **Rollback Time: 5 minutes**

```bash
# 1. Execute RLS migration
psql -U postgres -d billing_db -f migrations/003_row_level_security.sql

# 2. Test RLS is working
psql -U postgres -d billing_db -c "SELECT * FROM check_rls_status();"

# 3. Update application code to set tenant context
# In your application connection logic:
# await db.execute("SELECT set_tenant_context($1)", [tenantId])

# 4. Monitor for violations
psql -U postgres -d billing_db -c "SELECT * FROM vw_rls_violations;"
```

**Validation Tests:**
```sql
-- Test 1: Verify RLS is enabled
SELECT tablename, rls_enabled, policies_count 
FROM check_rls_status() 
WHERE rls_enabled = false;

-- Test 2: Test tenant isolation
SELECT set_tenant_context('550e8400-e29b-41d4-a716-446655440000');
SELECT COUNT(*) FROM organizations; -- Should return 1

-- Test 3: Check audit log
SELECT * FROM security_audit_log 
WHERE event_type = 'unauthorized_access_attempt'
ORDER BY timestamp DESC LIMIT 10;
```

### Day 2: Encryption at Rest (2-3 hours)
**Risk Level: HIGH** | **Downtime: None** | **Rollback Time: 1 hour**

```bash
# 1. Execute encryption migration
psql -U postgres -d billing_db -f migrations/004_encryption_at_rest.sql

# 2. Generate initial encryption keys
psql -U postgres -d billing_db -c "SELECT generate_encryption_key('master_key', 'data_encryption');"

# 3. Encrypt existing sensitive data (if any)
psql -U postgres -d billing_db -c "
DO \$\$
BEGIN
    UPDATE payment_methods 
    SET card_number_encrypted = encrypt_sensitive_data(card_number, NULL)
    WHERE card_number IS NOT NULL 
    AND card_number_encrypted IS NULL;
END \$\$;
"

# 4. Monitor encryption status
psql -U postgres -d billing_db -c "SELECT * FROM vw_encryption_status;"
```

**Validation Tests:**
```sql
-- Test 1: Verify encryption keys created
SELECT * FROM vw_key_usage;

-- Test 2: Test encryption/decryption
SELECT encrypt_sensitive_data('test-data', NULL);
SELECT decrypt_sensitive_data(
    encrypt_sensitive_data('test-data', NULL), 
    NULL
);

-- Test 3: Check encryption coverage
SELECT * FROM vw_encryption_status;
```

### Day 3: Critical Indexes (2-3 hours)
**Risk Level: LOW** | **Downtime: None** | **Rollback Time: 10 minutes**

```bash
# 1. Execute index creation (uses CONCURRENTLY - no locks)
psql -U postgres -d billing_db -f migrations/005_critical_indexes.sql

# 2. Analyze tables to update statistics
psql -U postgres -d billing_db -c "
ANALYZE usage_events;
ANALYZE subscriptions;
ANALYZE invoices;
ANALYZE billing_transactions;
"

# 3. Check index effectiveness
psql -U postgres -d billing_db -c "SELECT * FROM analyze_index_effectiveness();"

# 4. Look for missing indexes
psql -U postgres -d billing_db -c "SELECT * FROM suggest_missing_indexes();"
```

**Performance Validation:**
```sql
-- Test 1: Query performance test
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM usage_events 
WHERE organization_id = '550e8400-e29b-41d4-a716-446655440000'
AND timestamp > CURRENT_DATE - INTERVAL '30 days';

-- Test 2: Index usage statistics
SELECT * FROM vw_index_usage_stats 
WHERE usage_category IN ('UNUSED', 'RARELY_USED');

-- Test 3: Table bloat check
SELECT schemaname, tablename, bloat_percent 
FROM vw_schema_health 
WHERE bloat_percent > 20;
```

### Day 4: Audit Triggers (2-3 hours)
**Risk Level: MEDIUM** | **Downtime: None** | **Rollback Time: 15 minutes**

```bash
# 1. Execute audit trigger migration
psql -U postgres -d billing_db -f migrations/006_audit_triggers.sql

# 2. Test audit trail is working
psql -U postgres -d billing_db -c "
-- Perform test operation
UPDATE organizations 
SET updated_at = NOW() 
WHERE id = '550e8400-e29b-41d4-a716-446655440000';

-- Check audit trail
SELECT * FROM audit_trail 
WHERE table_name = 'organizations' 
ORDER BY occurred_at DESC LIMIT 1;
"

# 3. Verify audit trail integrity
psql -U postgres -d billing_db -c "SELECT * FROM verify_audit_trail_integrity();"

# 4. Check for suspicious activity
psql -U postgres -d billing_db -c "SELECT * FROM detect_suspicious_activity();"
```

**Compliance Validation:**
```sql
-- Test 1: PCI compliance audit
SELECT * FROM vw_pci_audit_trail LIMIT 10;

-- Test 2: GDPR compliance audit  
SELECT * FROM vw_gdpr_audit_trail LIMIT 10;

-- Test 3: Hash chain integrity
SELECT * FROM verify_audit_trail_integrity(
    CURRENT_DATE - INTERVAL '1 day',
    CURRENT_DATE
);
```

## Application Code Updates

### 1. Update Database Connection (Python/FastAPI)

```python
# backend/database.py
from backend.database_security import SecureDatabase

# Replace standard connection with secure connection
secure_db = SecureDatabase(DATABASE_URL)
await secure_db.initialize()

# In your endpoint handlers
@app.post("/api/v1/billing/usage")
async def record_usage(
    tenant_id: UUID,
    user_id: str,
    event: UsageEvent
):
    async with secure_db.get_secure_session(tenant_id, user_id) as session:
        # Session now has RLS context set
        # All queries will be tenant-scoped
        result = await session.execute(...)
```

### 2. Update Sensitive Data Handling

```python
from backend.database_security import EncryptionManager

encryption = EncryptionManager()

# Before storing payment method
payment_data = encryption.encrypt_dict(
    payment_method_dict,
    fields=["card_number", "cvv", "account_number"]
)

# When retrieving payment method
decrypted_data = encryption.decrypt_dict(
    payment_method_dict,
    fields=["card_number", "cvv", "account_number"]
)
```

### 3. Add Security Monitoring

```python
from backend.database_security import SecurityMonitor

monitor = SecurityMonitor(secure_db)

# Add to your monitoring service
async def security_check_task():
    while True:
        await monitor.check_rls_violations()
        await monitor.check_suspicious_activity()
        await monitor.verify_audit_integrity()
        await asyncio.sleep(300)  # Check every 5 minutes
```

## Rollback Procedures

### Rollback RLS
```sql
-- Disable RLS on all tables
ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions DISABLE ROW LEVEL SECURITY;
ALTER TABLE usage_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE invoices DISABLE ROW LEVEL SECURITY;
ALTER TABLE payment_methods DISABLE ROW LEVEL SECURITY;
ALTER TABLE billing_transactions DISABLE ROW LEVEL SECURITY;

-- Drop policies
DROP POLICY IF EXISTS tenant_isolation_policy ON organizations CASCADE;
-- ... repeat for all policies

-- Drop functions
DROP FUNCTION IF EXISTS set_tenant_context(UUID);
DROP FUNCTION IF EXISTS get_tenant_context();
```

### Rollback Encryption
```sql
-- Decrypt data back to plain text
UPDATE payment_methods 
SET card_number = decrypt_sensitive_data(card_number_encrypted, encryption_key_id),
    card_number_encrypted = NULL
WHERE card_number_encrypted IS NOT NULL;

-- Drop encryption infrastructure
DROP TABLE IF EXISTS encryption_keys CASCADE;
DROP TABLE IF EXISTS encryption_key_usage CASCADE;
DROP FUNCTION IF EXISTS encrypt_sensitive_data(TEXT, UUID);
DROP FUNCTION IF EXISTS decrypt_sensitive_data(BYTEA, UUID);
```

### Rollback Indexes
```sql
-- Drop all new indexes (they have specific names)
DROP INDEX IF EXISTS idx_usage_events_org_metric_time;
DROP INDEX IF EXISTS idx_usage_events_recent;
-- ... repeat for all indexes created

-- Restore any old indexes if needed
-- Check your backup for original index definitions
```

### Rollback Audit Triggers
```sql
-- Drop all audit triggers
DROP TRIGGER IF EXISTS audit_organizations ON organizations;
DROP TRIGGER IF EXISTS audit_subscriptions ON subscriptions;
DROP TRIGGER IF EXISTS audit_invoices ON invoices;
DROP TRIGGER IF EXISTS audit_payment_methods ON payment_methods;
DROP TRIGGER IF EXISTS audit_billing_transactions ON billing_transactions;

-- Drop audit infrastructure
DROP TABLE IF EXISTS audit_trail CASCADE;
DROP FUNCTION IF EXISTS audit_trigger_function();
DROP FUNCTION IF EXISTS create_audit_hash(TEXT, TEXT, UUID, JSONB, JSONB, TEXT);
```

## Monitoring & Alerts

### Key Metrics to Monitor

1. **RLS Violations**
   ```sql
   SELECT COUNT(*) as violation_count 
   FROM vw_rls_violations 
   WHERE timestamp > NOW() - INTERVAL '1 hour';
   ```
   Alert if: > 10 violations/hour

2. **Encryption Coverage**
   ```sql
   SELECT table_name, encryption_percentage 
   FROM vw_encryption_status 
   WHERE encryption_percentage < 100;
   ```
   Alert if: < 100% for PCI tables

3. **Index Effectiveness**
   ```sql
   SELECT index_name, effectiveness_score 
   FROM analyze_index_effectiveness() 
   WHERE effectiveness_score < 50;
   ```
   Alert if: Key indexes < 50% effective

4. **Audit Trail Integrity**
   ```sql
   SELECT * FROM verify_audit_trail_integrity();
   ```
   Alert if: is_valid = false

### Grafana Dashboard Queries

```sql
-- RLS violation rate
SELECT 
    date_trunc('hour', timestamp) as time,
    COUNT(*) as violations
FROM security_audit_log
WHERE event_type = 'unauthorized_access_attempt'
AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1;

-- Query performance after indexes
SELECT 
    date_trunc('minute', query_start) as time,
    AVG(duration) as avg_duration,
    MAX(duration) as max_duration,
    COUNT(*) as query_count
FROM pg_stat_statements
WHERE query LIKE '%usage_events%'
GROUP BY 1;

-- Audit trail growth
SELECT 
    date_trunc('hour', occurred_at) as time,
    COUNT(*) as audit_events,
    pg_size_pretty(SUM(pg_column_size(old_values) + pg_column_size(new_values))) as data_size
FROM audit_trail
WHERE occurred_at > NOW() - INTERVAL '24 hours'
GROUP BY 1;
```

## Performance Benchmarks

### Before Implementation
- Query time (p95): 250ms
- Events/minute: 850,000
- Security score: 45/100

### Expected After Implementation  
- Query time (p95): 85ms (66% improvement)
- Events/minute: 1,000,000+ (18% improvement)
- Security score: 90/100 (100% improvement)

### Actual Results (to be filled)
- [ ] Query time (p95): ___ms
- [ ] Events/minute: ___
- [ ] Security score: ___/100
- [ ] RLS violations detected: ___
- [ ] Audit events captured: ___

## Success Criteria

- [x] All 4 migrations executed without errors
- [ ] No RLS violations in first 24 hours
- [ ] 100% encryption coverage on PCI data
- [ ] Query performance improved by >50%
- [ ] Audit trail capturing all changes
- [ ] Zero data integrity issues
- [ ] Application functioning normally
- [ ] Monitoring alerts configured

## Support & Escalation

**Primary Contact:** Database Team  
**Slack Channel:** #database-ops  
**On-Call:** PagerDuty - Database Team  
**Documentation:** This guide + migration scripts  
**Rollback Authority:** Senior DBA or CTO  

## Post-Implementation Tasks

1. **Day 1 After:** 
   - Monitor all metrics closely
   - Review audit logs for anomalies
   - Validate application functionality

2. **Week 1 After:**
   - Performance tuning based on actual load
   - Key rotation test
   - Disaster recovery test

3. **Month 1 After:**
   - Security audit
   - Compliance review
   - Performance optimization round 2
