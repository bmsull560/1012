# Security Framework Review - ValueVerse Billing System

## Current Security Assessment

### Security Maturity Level: **BASIC (Level 2/5)**

| Domain | Current State | Target State | Gap |
|--------|--------------|--------------|-----|
| Access Control | Application-only | Database + Application | HIGH |
| Encryption | TLS only | TLS + At-rest + Field-level | HIGH |
| Auditing | Basic logs | Immutable audit trail | MEDIUM |
| Compliance | None | PCI DSS, GDPR, SOC2 | CRITICAL |
| Vulnerability Mgmt | None | Automated scanning | HIGH |

## Access Control Enhancement

### 1. Role-Based Access Control (RBAC)

```sql
-- Create security roles hierarchy
CREATE ROLE billing_admin;
CREATE ROLE billing_operator;
CREATE ROLE billing_readonly;
CREATE ROLE billing_api;
CREATE ROLE tenant_user;

-- Admin: Full access
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO billing_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO billing_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO billing_admin;

-- Operator: Read/Write on operational tables
GRANT SELECT, INSERT, UPDATE ON usage_events TO billing_operator;
GRANT SELECT, INSERT, UPDATE ON invoices TO billing_operator;
GRANT SELECT ON subscriptions TO billing_operator;
REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM billing_operator;

-- Readonly: Select only
GRANT SELECT ON ALL TABLES IN SCHEMA public TO billing_readonly;
REVOKE ALL ON sensitive_data FROM billing_readonly;

-- API: Limited to procedures
GRANT EXECUTE ON FUNCTION fn_record_usage TO billing_api;
GRANT EXECUTE ON FUNCTION fn_generate_invoice TO billing_api;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM billing_api;

-- Tenant: Row-level access only
GRANT SELECT ON organizations TO tenant_user;
GRANT SELECT ON subscriptions TO tenant_user;
GRANT SELECT ON invoices TO tenant_user;
-- RLS will filter rows
```

### 2. Attribute-Based Access Control (ABAC)

```sql
-- Create security attributes table
CREATE TABLE security_attributes (
    user_id UUID PRIMARY KEY,
    attributes JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ABAC policy function
CREATE OR REPLACE FUNCTION fn_check_abac_policy(
    user_id UUID,
    resource_type TEXT,
    action TEXT,
    resource_attributes JSONB
) RETURNS BOOLEAN AS $$
DECLARE
    user_attributes JSONB;
    policy_result BOOLEAN DEFAULT FALSE;
BEGIN
    -- Get user attributes
    SELECT attributes INTO user_attributes
    FROM security_attributes
    WHERE security_attributes.user_id = $1;
    
    -- Evaluate policies
    CASE resource_type
        WHEN 'invoice' THEN
            -- Can only view invoices from same region
            policy_result := 
                user_attributes->>'region' = resource_attributes->>'region' OR
                user_attributes->>'role' = 'admin';
                
        WHEN 'payment_method' THEN
            -- Can only modify if owner or admin
            policy_result := 
                user_attributes->>'organization_id' = resource_attributes->>'organization_id' OR
                user_attributes->>'role' = 'admin';
                
        ELSE
            policy_result := FALSE;
    END CASE;
    
    -- Log access attempt
    INSERT INTO access_log (user_id, resource_type, action, granted, timestamp)
    VALUES (user_id, resource_type, action, policy_result, NOW());
    
    RETURN policy_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 3. Database Authentication

```sql
-- Enable certificate-based authentication
ALTER SYSTEM SET ssl = 'on';
ALTER SYSTEM SET ssl_cert_file = '/etc/postgresql/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/postgresql/server.key';
ALTER SYSTEM SET ssl_ca_file = '/etc/postgresql/ca.crt';
ALTER SYSTEM SET ssl_crl_file = '/etc/postgresql/crl.pem';

-- Enforce SSL for all connections
-- pg_hba.conf
hostssl all all 0.0.0.0/0 cert clientcert=verify-full

-- Create certificate-mapped users
CREATE USER billing_api_prod WITH ENCRYPTED PASSWORD NULL;
ALTER USER billing_api_prod SET sslmode = 'require';
ALTER USER billing_api_prod SET sslcert = '/certs/api_prod.crt';

-- Password policy
CREATE EXTENSION IF NOT EXISTS credcheck;
ALTER SYSTEM SET credcheck.password_min_length = 12;
ALTER SYSTEM SET credcheck.password_min_special = 2;
ALTER SYSTEM SET credcheck.password_min_digits = 2;
ALTER SYSTEM SET credcheck.password_max_repeat = 2;
```

## Data Encryption Strategy

### 1. Encryption at Rest

```sql
-- Enable Transparent Data Encryption (TDE)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypted tablespace
CREATE TABLESPACE encrypted_space
LOCATION '/mnt/encrypted'
WITH (encryption_method = 'AES256');

-- Move sensitive tables to encrypted tablespace
ALTER TABLE payment_methods SET TABLESPACE encrypted_space;
ALTER TABLE billing_transactions SET TABLESPACE encrypted_space;
ALTER TABLE audit_trail SET TABLESPACE encrypted_space;

-- Column-level encryption for PII
ALTER TABLE organizations ADD COLUMN tax_id_encrypted BYTEA;

-- Encryption functions
CREATE OR REPLACE FUNCTION fn_encrypt_pii(
    plain_text TEXT,
    key_id UUID DEFAULT NULL
) RETURNS BYTEA AS $$
DECLARE
    encryption_key BYTEA;
BEGIN
    -- Get or generate key
    SELECT key INTO encryption_key
    FROM encryption_keys
    WHERE id = COALESCE(key_id, get_current_key_id())
    AND active = TRUE;
    
    -- Encrypt with AES-256-GCM
    RETURN pgp_sym_encrypt(
        plain_text,
        encryption_key,
        'cipher-algo=aes256, compress-algo=0'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION fn_decrypt_pii(
    encrypted_data BYTEA,
    key_id UUID DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    decryption_key BYTEA;
BEGIN
    -- Audit decryption attempt
    INSERT INTO decryption_audit_log (user_id, timestamp, resource)
    VALUES (current_user, NOW(), 'pii_data');
    
    -- Get key
    SELECT key INTO decryption_key
    FROM encryption_keys
    WHERE id = COALESCE(key_id, extract_key_id(encrypted_data))
    AND active = TRUE;
    
    -- Decrypt
    RETURN pgp_sym_decrypt(encrypted_data, decryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 2. Field-Level Encryption

```sql
-- Sensitive fields encryption
CREATE TABLE payment_methods_secure (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    -- Encrypted fields
    card_number_encrypted BYTEA,
    card_number_last4 VARCHAR(4), -- For display
    cvv_encrypted BYTEA,
    account_number_encrypted BYTEA,
    routing_number_encrypted BYTEA,
    -- Metadata
    key_version INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trigger for automatic encryption
CREATE OR REPLACE FUNCTION fn_encrypt_payment_method()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.card_number_encrypted IS NOT NULL THEN
        NEW.card_number_encrypted := fn_encrypt_pii(NEW.card_number_encrypted::TEXT);
        NEW.card_number_last4 := RIGHT(NEW.card_number_encrypted::TEXT, 4);
    END IF;
    
    IF NEW.account_number_encrypted IS NOT NULL THEN
        NEW.account_number_encrypted := fn_encrypt_pii(NEW.account_number_encrypted::TEXT);
    END IF;
    
    NEW.key_version := get_current_key_version();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER encrypt_payment_data
BEFORE INSERT OR UPDATE ON payment_methods_secure
FOR EACH ROW EXECUTE FUNCTION fn_encrypt_payment_method();
```

### 3. Key Management

```sql
-- Key management table
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key BYTEA NOT NULL,
    algorithm VARCHAR(50) NOT NULL DEFAULT 'AES-256-GCM',
    created_at TIMESTAMP DEFAULT NOW(),
    rotated_at TIMESTAMP,
    expires_at TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    purpose VARCHAR(100),
    CHECK (LENGTH(key) = 32) -- 256 bits
);

-- Key rotation procedure
CREATE OR REPLACE FUNCTION fn_rotate_encryption_keys()
RETURNS void AS $$
DECLARE
    old_key_id UUID;
    new_key_id UUID;
BEGIN
    -- Deactivate old key
    UPDATE encryption_keys
    SET active = FALSE, rotated_at = NOW()
    WHERE active = TRUE
    RETURNING id INTO old_key_id;
    
    -- Generate new key
    INSERT INTO encryption_keys (key, active, purpose)
    VALUES (gen_random_bytes(32), TRUE, 'primary')
    RETURNING id INTO new_key_id;
    
    -- Re-encrypt sensitive data
    UPDATE payment_methods_secure
    SET card_number_encrypted = fn_reencrypt(
        card_number_encrypted, old_key_id, new_key_id
    )
    WHERE key_version = old_key_id;
    
    RAISE NOTICE 'Key rotation completed: % -> %', old_key_id, new_key_id;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly key rotation
SELECT cron.schedule('rotate-keys', '0 0 1 * *', 'SELECT fn_rotate_encryption_keys()');
```

## Compliance Framework

### 1. GDPR Compliance

```sql
-- Data subject rights implementation
CREATE TABLE gdpr_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL,
    request_type VARCHAR(50) CHECK (request_type IN (
        'access', 'rectification', 'erasure', 'portability', 'restriction'
    )),
    status VARCHAR(50) DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB
);

-- Right to be forgotten
CREATE OR REPLACE FUNCTION fn_gdpr_erasure(subject_id UUID)
RETURNS void AS $$
BEGIN
    -- Anonymize personal data
    UPDATE organizations
    SET 
        name = 'REDACTED-' || id,
        billing_email = 'redacted@example.com',
        tax_id = 'REDACTED',
        billing_address = '{}',
        metadata = '{"gdpr_erased": true}'::JSONB
    WHERE id = subject_id;
    
    -- Delete payment methods
    DELETE FROM payment_methods WHERE organization_id = subject_id;
    
    -- Anonymize invoices (keep for legal requirements)
    UPDATE invoices
    SET metadata = jsonb_set(metadata, '{gdpr_erased}', 'true')
    WHERE organization_id = subject_id;
    
    -- Log erasure
    INSERT INTO gdpr_requests (subject_id, request_type, status, completed_at)
    VALUES (subject_id, 'erasure', 'completed', NOW());
END;
$$ LANGUAGE plpgsql;

-- Data portability
CREATE OR REPLACE FUNCTION fn_gdpr_export(subject_id UUID)
RETURNS JSON AS $$
DECLARE
    export_data JSON;
BEGIN
    SELECT json_build_object(
        'organization', row_to_json(o),
        'subscriptions', json_agg(DISTINCT s),
        'invoices', json_agg(DISTINCT i),
        'usage_events', json_agg(DISTINCT ue)
    ) INTO export_data
    FROM organizations o
    LEFT JOIN subscriptions s ON o.id = s.organization_id
    LEFT JOIN invoices i ON o.id = i.organization_id
    LEFT JOIN usage_events ue ON o.id = ue.organization_id
    WHERE o.id = subject_id
    GROUP BY o.id;
    
    -- Log export
    INSERT INTO gdpr_requests (subject_id, request_type, status, completed_at)
    VALUES (subject_id, 'portability', 'completed', NOW());
    
    RETURN export_data;
END;
$$ LANGUAGE plpgsql;
```

### 2. PCI DSS Compliance

```sql
-- PCI DSS requirements implementation
CREATE TABLE pci_audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    resource_type VARCHAR(50),
    resource_id UUID,
    action VARCHAR(50),
    result VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW(),
    details JSONB
) PARTITION BY RANGE (timestamp);

-- Create partitions for audit retention
CREATE TABLE pci_audit_log_2024_01 
PARTITION OF pci_audit_log
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Cardholder Data Environment (CDE) isolation
CREATE SCHEMA cde_data;

-- Move sensitive tables to CDE schema
ALTER TABLE payment_methods SET SCHEMA cde_data;
ALTER TABLE billing_transactions SET SCHEMA cde_data;

-- Restrict CDE access
REVOKE ALL ON SCHEMA cde_data FROM PUBLIC;
GRANT USAGE ON SCHEMA cde_data TO pci_compliant_role;

-- Tokenization function
CREATE OR REPLACE FUNCTION fn_tokenize_card(
    card_number TEXT
) RETURNS VARCHAR AS $$
DECLARE
    token VARCHAR;
BEGIN
    -- Generate secure token
    token := 'tok_' || encode(digest(card_number || gen_random_uuid()::TEXT, 'sha256'), 'hex');
    
    -- Store mapping securely
    INSERT INTO cde_data.tokenization_vault (token, encrypted_pan, created_at)
    VALUES (token, fn_encrypt_pii(card_number), NOW());
    
    -- Audit tokenization
    INSERT INTO pci_audit_log (event_type, action, result, details)
    VALUES ('tokenization', 'create', 'success', 
            jsonb_build_object('token', token, 'last4', RIGHT(card_number, 4)));
    
    RETURN token;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 3. Audit Trail

```sql
-- Immutable audit trail
CREATE TABLE audit_trail_immutable (
    id BIGSERIAL,
    event_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) REFERENCES audit_trail_immutable(event_hash),
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    user_id UUID,
    organization_id UUID,
    record_id UUID NOT NULL,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    signature TEXT,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Hash chain function
CREATE OR REPLACE FUNCTION fn_create_audit_hash(
    table_name TEXT,
    operation TEXT,
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    previous_hash TEXT
) RETURNS VARCHAR AS $$
DECLARE
    data_to_hash TEXT;
    event_hash VARCHAR;
BEGIN
    data_to_hash := COALESCE(previous_hash, '') || '|' ||
                    table_name || '|' ||
                    operation || '|' ||
                    record_id::TEXT || '|' ||
                    COALESCE(old_values::TEXT, '') || '|' ||
                    COALESCE(new_values::TEXT, '') || '|' ||
                    NOW()::TEXT;
    
    event_hash := encode(digest(data_to_hash, 'sha256'), 'hex');
    
    RETURN event_hash;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Generic audit trigger
CREATE OR REPLACE FUNCTION fn_audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    old_values JSONB;
    new_values JSONB;
    previous_hash VARCHAR;
    event_hash VARCHAR;
BEGIN
    -- Get previous hash
    SELECT audit_trail_immutable.event_hash INTO previous_hash
    FROM audit_trail_immutable
    ORDER BY id DESC
    LIMIT 1;
    
    -- Prepare values
    IF TG_OP = 'DELETE' THEN
        old_values := row_to_json(OLD);
        new_values := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        old_values := row_to_json(OLD);
        new_values := row_to_json(NEW);
    ELSE -- INSERT
        old_values := NULL;
        new_values := row_to_json(NEW);
    END IF;
    
    -- Create hash
    event_hash := fn_create_audit_hash(
        TG_TABLE_NAME,
        TG_OP,
        COALESCE(NEW.id, OLD.id),
        old_values,
        new_values,
        previous_hash
    );
    
    -- Insert audit record
    INSERT INTO audit_trail_immutable (
        event_hash,
        previous_hash,
        table_name,
        operation,
        user_id,
        organization_id,
        record_id,
        old_values,
        new_values
    ) VALUES (
        event_hash,
        previous_hash,
        TG_TABLE_NAME,
        TG_OP,
        current_setting('app.current_user', true)::UUID,
        current_setting('app.current_tenant', true)::UUID,
        COALESCE(NEW.id, OLD.id),
        old_values,
        new_values
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply audit triggers to sensitive tables
CREATE TRIGGER audit_organizations
AFTER INSERT OR UPDATE OR DELETE ON organizations
FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();

CREATE TRIGGER audit_payment_methods
AFTER INSERT OR UPDATE OR DELETE ON payment_methods
FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();

CREATE TRIGGER audit_invoices
AFTER INSERT OR UPDATE OR DELETE ON invoices
FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();
```

## Security Vulnerability Assessment

### 1. SQL Injection Prevention

```sql
-- Parameterized query enforcement
CREATE OR REPLACE FUNCTION fn_safe_query(
    query_template TEXT,
    params VARIADIC TEXT[]
) RETURNS SETOF RECORD AS $$
BEGIN
    -- Validate query template
    IF query_template ~ ';|--|/\*|\*/' THEN
        RAISE EXCEPTION 'Potentially unsafe query detected';
    END IF;
    
    -- Execute with parameters
    RETURN QUERY EXECUTE query_template USING params;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Input validation function
CREATE OR REPLACE FUNCTION fn_validate_input(
    input_text TEXT,
    input_type TEXT
) RETURNS TEXT AS $$
BEGIN
    CASE input_type
        WHEN 'email' THEN
            IF input_text !~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' THEN
                RAISE EXCEPTION 'Invalid email format';
            END IF;
        WHEN 'uuid' THEN
            IF input_text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
                RAISE EXCEPTION 'Invalid UUID format';
            END IF;
        WHEN 'alphanumeric' THEN
            IF input_text ~ '[^a-zA-Z0-9]' THEN
                RAISE EXCEPTION 'Only alphanumeric characters allowed';
            END IF;
    END CASE;
    
    RETURN input_text;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

### 2. Security Monitoring

```sql
-- Real-time security monitoring
CREATE OR REPLACE FUNCTION fn_security_monitor()
RETURNS TABLE (
    alert_type VARCHAR,
    severity VARCHAR,
    description TEXT,
    details JSONB
) AS $$
BEGIN
    -- Check for suspicious login patterns
    RETURN QUERY
    SELECT 
        'suspicious_login' as alert_type,
        'HIGH' as severity,
        'Multiple failed login attempts' as description,
        jsonb_build_object(
            'user_id', user_id,
            'attempts', COUNT(*),
            'ip_addresses', array_agg(DISTINCT ip_address)
        ) as details
    FROM login_attempts
    WHERE success = FALSE
    AND timestamp > NOW() - INTERVAL '10 minutes'
    GROUP BY user_id
    HAVING COUNT(*) > 5;
    
    -- Check for privilege escalation attempts
    RETURN QUERY
    SELECT 
        'privilege_escalation' as alert_type,
        'CRITICAL' as severity,
        'Unauthorized privilege escalation attempt' as description,
        jsonb_build_object(
            'user_id', user_id,
            'attempted_role', attempted_role,
            'timestamp', timestamp
        ) as details
    FROM audit_trail
    WHERE operation = 'GRANT'
    AND result = 'denied'
    AND timestamp > NOW() - INTERVAL '1 hour';
    
    -- Check for data exfiltration
    RETURN QUERY
    SELECT 
        'data_exfiltration' as alert_type,
        'HIGH' as severity,
        'Potential data exfiltration detected' as description,
        jsonb_build_object(
            'user_id', user_id,
            'rows_accessed', SUM(rows_accessed),
            'tables', array_agg(DISTINCT table_name)
        ) as details
    FROM query_log
    WHERE timestamp > NOW() - INTERVAL '10 minutes'
    GROUP BY user_id
    HAVING SUM(rows_accessed) > 100000;
END;
$$ LANGUAGE plpgsql;
```

## Implementation Priority

| Security Control | Priority | Effort | Impact | Timeline |
|-----------------|----------|--------|--------|----------|
| Row-Level Security | CRITICAL | Low | High | Week 1 |
| Encryption at Rest | CRITICAL | Medium | High | Week 1 |
| Audit Trail | HIGH | Medium | High | Week 2 |
| RBAC Implementation | HIGH | Low | High | Week 2 |
| PCI Tokenization | CRITICAL | High | Critical | Week 3 |
| GDPR Compliance | HIGH | Medium | High | Week 4 |
| Key Management | HIGH | High | High | Month 2 |
| Security Monitoring | MEDIUM | Medium | Medium | Month 2 |

## Security Checklist

- [ ] Enable SSL/TLS for all connections
- [ ] Implement Row-Level Security
- [ ] Enable encryption at rest
- [ ] Create audit trail
- [ ] Implement RBAC
- [ ] Add field-level encryption for PII
- [ ] Setup key rotation
- [ ] Configure security monitoring
- [ ] Implement GDPR compliance
- [ ] Add PCI DSS tokenization
- [ ] Create security dashboards
- [ ] Document security procedures
- [ ] Conduct penetration testing
- [ ] Implement WAF rules
- [ ] Setup DDoS protection
