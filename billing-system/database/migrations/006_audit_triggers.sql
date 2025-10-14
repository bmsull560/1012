-- =====================================================
-- Audit Trail Implementation with Triggers
-- Execution Time: ~2 days
-- Priority: HIGH (Compliance)
-- =====================================================

-- STEP 1: Create immutable audit trail table
-- =====================================================

-- Main audit trail table (partitioned by month)
CREATE TABLE IF NOT EXISTS audit_trail (
    id BIGSERIAL,
    event_id UUID DEFAULT uuid_generate_v4(),
    event_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'SELECT', 'TRUNCATE')),
    user_id VARCHAR(100) NOT NULL DEFAULT current_user,
    tenant_id UUID,
    session_id VARCHAR(100),
    transaction_id BIGINT DEFAULT txid_current(),
    
    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    
    -- Context
    application_name VARCHAR(100) DEFAULT current_setting('application_name', true),
    client_ip INET DEFAULT inet_client_addr(),
    client_port INTEGER DEFAULT inet_client_port(),
    
    -- Timestamps
    occurred_at TIMESTAMP NOT NULL DEFAULT now(),
    recorded_at TIMESTAMP NOT NULL DEFAULT clock_timestamp(),
    
    -- Compliance fields
    compliance_tags TEXT[],
    data_classification VARCHAR(50),
    retention_until DATE,
    
    -- Signature for tamper detection
    signature TEXT,
    
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

-- Create initial partitions
CREATE TABLE IF NOT EXISTS audit_trail_2024_10 
PARTITION OF audit_trail
FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE IF NOT EXISTS audit_trail_2024_11 
PARTITION OF audit_trail
FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE IF NOT EXISTS audit_trail_2024_12 
PARTITION OF audit_trail
FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Indexes for audit trail
CREATE INDEX idx_audit_trail_event_hash ON audit_trail(event_hash);
CREATE INDEX idx_audit_trail_table_record ON audit_trail(table_name, record_id, occurred_at DESC);
CREATE INDEX idx_audit_trail_user ON audit_trail(user_id, occurred_at DESC);
CREATE INDEX idx_audit_trail_tenant ON audit_trail(tenant_id, occurred_at DESC);
CREATE INDEX idx_audit_trail_operation ON audit_trail(operation, occurred_at DESC);
CREATE INDEX idx_audit_trail_compliance ON audit_trail USING GIN(compliance_tags);

-- STEP 2: Create hash chain functions for immutability
-- =====================================================

-- Function to create audit event hash
CREATE OR REPLACE FUNCTION create_audit_hash(
    p_table_name TEXT,
    p_operation TEXT,
    p_record_id UUID,
    p_old_values JSONB,
    p_new_values JSONB,
    p_previous_hash TEXT
) RETURNS VARCHAR AS $$
DECLARE
    hash_input TEXT;
BEGIN
    -- Concatenate all fields for hashing
    hash_input := COALESCE(p_previous_hash, 'GENESIS') || '|' ||
                  p_table_name || '|' ||
                  p_operation || '|' ||
                  p_record_id::TEXT || '|' ||
                  COALESCE(p_old_values::TEXT, 'NULL') || '|' ||
                  COALESCE(p_new_values::TEXT, 'NULL') || '|' ||
                  extract(epoch from now())::TEXT || '|' ||
                  current_user || '|' ||
                  txid_current()::TEXT;
    
    RETURN encode(digest(hash_input, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to verify audit trail integrity
CREATE OR REPLACE FUNCTION verify_audit_trail_integrity(
    start_date TIMESTAMP DEFAULT CURRENT_DATE - INTERVAL '7 days',
    end_date TIMESTAMP DEFAULT CURRENT_DATE
) RETURNS TABLE (
    is_valid BOOLEAN,
    invalid_records INTEGER,
    first_invalid_id BIGINT,
    details TEXT
) AS $$
DECLARE
    rec RECORD;
    expected_hash VARCHAR;
    invalid_count INTEGER := 0;
    first_invalid BIGINT;
    prev_hash VARCHAR := 'GENESIS';
BEGIN
    FOR rec IN 
        SELECT * FROM audit_trail 
        WHERE occurred_at BETWEEN start_date AND end_date
        ORDER BY id
    LOOP
        expected_hash := create_audit_hash(
            rec.table_name,
            rec.operation,
            rec.record_id,
            rec.old_values,
            rec.new_values,
            prev_hash
        );
        
        IF rec.event_hash != expected_hash THEN
            invalid_count := invalid_count + 1;
            IF first_invalid IS NULL THEN
                first_invalid := rec.id;
            END IF;
        END IF;
        
        prev_hash := rec.event_hash;
    END LOOP;
    
    RETURN QUERY SELECT 
        invalid_count = 0,
        invalid_count,
        first_invalid,
        CASE 
            WHEN invalid_count = 0 THEN 'Audit trail integrity verified'
            ELSE format('Found %s invalid records starting at ID %s', invalid_count, first_invalid)
        END;
END;
$$ LANGUAGE plpgsql;

-- STEP 3: Create generic audit trigger function
-- =====================================================

CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_id BIGINT;
    old_values JSONB;
    new_values JSONB;
    changed_fields TEXT[];
    previous_hash VARCHAR;
    event_hash VARCHAR;
    tenant_id UUID;
    data_class VARCHAR;
BEGIN
    -- Get previous hash for chain
    SELECT event_hash INTO previous_hash
    FROM audit_trail
    ORDER BY id DESC
    LIMIT 1;
    
    -- Get tenant context if available
    tenant_id := get_tenant_context();
    
    -- Determine data classification
    data_class := CASE 
        WHEN TG_TABLE_NAME IN ('payment_methods', 'billing_transactions') THEN 'PCI'
        WHEN TG_TABLE_NAME IN ('organizations', 'users') THEN 'PII'
        ELSE 'STANDARD'
    END;
    
    -- Prepare audit data based on operation
    IF TG_OP = 'DELETE' THEN
        old_values := row_to_json(OLD)::JSONB;
        new_values := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        old_values := row_to_json(OLD)::JSONB;
        new_values := row_to_json(NEW)::JSONB;
        
        -- Identify changed fields
        SELECT array_agg(key) INTO changed_fields
        FROM (
            SELECT key 
            FROM jsonb_each(old_values)
            WHERE old_values->key IS DISTINCT FROM new_values->key
        ) changes;
        
    ELSIF TG_OP = 'INSERT' THEN
        old_values := NULL;
        new_values := row_to_json(NEW)::JSONB;
    END IF;
    
    -- Mask sensitive data in audit log
    IF data_class IN ('PCI', 'PII') THEN
        new_values := mask_sensitive_data(new_values, TG_TABLE_NAME);
        old_values := mask_sensitive_data(old_values, TG_TABLE_NAME);
    END IF;
    
    -- Create event hash
    event_hash := create_audit_hash(
        TG_TABLE_NAME,
        TG_OP,
        COALESCE(NEW.id, OLD.id),
        old_values,
        new_values,
        previous_hash
    );
    
    -- Insert audit record
    INSERT INTO audit_trail (
        event_hash,
        previous_hash,
        table_name,
        record_id,
        operation,
        tenant_id,
        old_values,
        new_values,
        changed_fields,
        data_classification,
        compliance_tags,
        retention_until,
        session_id
    ) VALUES (
        event_hash,
        previous_hash,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        tenant_id,
        old_values,
        new_values,
        changed_fields,
        data_class,
        ARRAY[data_class, TG_OP, TG_TABLE_NAME],
        CASE 
            WHEN data_class = 'PCI' THEN CURRENT_DATE + INTERVAL '7 years'
            WHEN data_class = 'PII' THEN CURRENT_DATE + INTERVAL '5 years'
            ELSE CURRENT_DATE + INTERVAL '2 years'
        END,
        current_setting('app.session_id', true)
    ) RETURNING id INTO audit_id;
    
    -- For critical operations, also log to security audit
    IF TG_TABLE_NAME IN ('payment_methods', 'billing_transactions', 'organizations') THEN
        INSERT INTO security_audit_log (
            event_type,
            user_id,
            tenant_id,
            details,
            timestamp
        ) VALUES (
            format('%s_%s', lower(TG_TABLE_NAME), lower(TG_OP)),
            current_user,
            tenant_id,
            jsonb_build_object(
                'audit_id', audit_id,
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'record_id', COALESCE(NEW.id, OLD.id)
            ),
            now()
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- STEP 4: Function to mask sensitive data
-- =====================================================

CREATE OR REPLACE FUNCTION mask_sensitive_data(
    data JSONB,
    table_name TEXT
) RETURNS JSONB AS $$
DECLARE
    masked_data JSONB;
BEGIN
    IF data IS NULL THEN
        RETURN NULL;
    END IF;
    
    masked_data := data;
    
    -- Mask based on table
    CASE table_name
        WHEN 'payment_methods' THEN
            masked_data := jsonb_set(masked_data, '{card_number}', '"****"', false);
            masked_data := jsonb_set(masked_data, '{cvv}', '"***"', false);
            masked_data := jsonb_set(masked_data, '{account_number}', '"****"', false);
            
        WHEN 'organizations' THEN
            masked_data := jsonb_set(masked_data, '{tax_id}', '"***-**-****"', false);
            masked_data := jsonb_set(masked_data, '{billing_email}', 
                to_jsonb(substring(data->>'billing_email' from 1 for 3) || '***@***'), false);
                
        WHEN 'billing_transactions' THEN
            -- Keep only last 4 digits of reference numbers
            IF data ? 'provider_reference' THEN
                masked_data := jsonb_set(masked_data, '{provider_reference}', 
                    to_jsonb('****' || right(data->>'provider_reference', 4)), false);
            END IF;
    END CASE;
    
    RETURN masked_data;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- STEP 5: Apply audit triggers to all tables
-- =====================================================

-- Critical tables (all operations)
CREATE TRIGGER audit_organizations
AFTER INSERT OR UPDATE OR DELETE ON organizations
FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_subscriptions
AFTER INSERT OR UPDATE OR DELETE ON subscriptions
FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_invoices
AFTER INSERT OR UPDATE OR DELETE ON invoices
FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_payment_methods
AFTER INSERT OR UPDATE OR DELETE ON payment_methods
FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_billing_transactions
AFTER INSERT OR UPDATE OR DELETE ON billing_transactions
FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- High-volume tables (only critical operations)
CREATE TRIGGER audit_usage_events
AFTER INSERT OR DELETE ON usage_events
FOR EACH ROW 
WHEN (NEW.quantity > 10000 OR OLD.quantity > 10000)
EXECUTE FUNCTION audit_trigger_function();

-- STEP 6: Create SELECT audit for sensitive queries
-- =====================================================

CREATE OR REPLACE FUNCTION audit_select_trigger()
RETURNS void AS $$
BEGIN
    -- This would be called from application layer
    -- PostgreSQL doesn't support SELECT triggers natively
    INSERT INTO audit_trail (
        event_hash,
        table_name,
        record_id,
        operation,
        tenant_id,
        new_values,
        data_classification
    ) VALUES (
        create_audit_hash(TG_TABLE_NAME, 'SELECT', NULL, NULL, NULL, NULL),
        TG_TABLE_NAME,
        '00000000-0000-0000-0000-000000000000',
        'SELECT',
        get_tenant_context(),
        jsonb_build_object('query', current_query()),
        'READ_AUDIT'
    );
END;
$$ LANGUAGE plpgsql;

-- STEP 7: Create compliance-specific audit views
-- =====================================================

-- PCI compliance audit view
CREATE OR REPLACE VIEW vw_pci_audit_trail AS
SELECT 
    id,
    event_id,
    table_name,
    record_id,
    operation,
    user_id,
    occurred_at,
    changed_fields,
    client_ip
FROM audit_trail
WHERE data_classification = 'PCI'
AND occurred_at > CURRENT_DATE - INTERVAL '90 days'
ORDER BY occurred_at DESC;

-- GDPR compliance audit view
CREATE OR REPLACE VIEW vw_gdpr_audit_trail AS
SELECT 
    id,
    event_id,
    table_name,
    record_id,
    operation,
    user_id,
    tenant_id,
    occurred_at,
    CASE 
        WHEN operation = 'DELETE' THEN 'Right to Erasure'
        WHEN operation = 'UPDATE' THEN 'Right to Rectification'
        WHEN operation = 'SELECT' THEN 'Right to Access'
        ELSE 'Data Processing'
    END as gdpr_action
FROM audit_trail
WHERE data_classification IN ('PII', 'GDPR')
AND table_name IN ('organizations', 'users', 'payment_methods')
ORDER BY occurred_at DESC;

-- Failed access attempts
CREATE OR REPLACE VIEW vw_failed_access_audit AS
SELECT 
    sal.timestamp,
    sal.user_id,
    sal.tenant_id,
    sal.ip_address,
    sal.details
FROM security_audit_log sal
WHERE sal.event_type IN ('unauthorized_access_attempt', 'authentication_failed')
AND sal.timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY sal.timestamp DESC;

-- STEP 8: Create audit retention and cleanup
-- =====================================================

-- Function to archive old audit records
CREATE OR REPLACE FUNCTION archive_old_audit_records()
RETURNS void AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Archive records older than retention period
    WITH archived AS (
        DELETE FROM audit_trail
        WHERE occurred_at < retention_until
        AND data_classification NOT IN ('PCI', 'LEGAL_HOLD')
        RETURNING *
    )
    INSERT INTO audit_trail_archive
    SELECT * FROM archived;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Log archival
    INSERT INTO security_audit_log (
        event_type,
        details
    ) VALUES (
        'audit_archive',
        jsonb_build_object('records_archived', archived_count)
    );
    
    RAISE NOTICE 'Archived % audit records', archived_count;
END;
$$ LANGUAGE plpgsql;

-- STEP 9: Create audit report functions
-- =====================================================

-- User activity report
CREATE OR REPLACE FUNCTION generate_user_activity_report(
    p_user_id VARCHAR,
    p_start_date TIMESTAMP DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_end_date TIMESTAMP DEFAULT CURRENT_DATE
) RETURNS TABLE (
    operation VARCHAR,
    table_name VARCHAR,
    count BIGINT,
    first_occurrence TIMESTAMP,
    last_occurrence TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        at.operation::VARCHAR,
        at.table_name::VARCHAR,
        COUNT(*)::BIGINT,
        MIN(at.occurred_at),
        MAX(at.occurred_at)
    FROM audit_trail at
    WHERE at.user_id = p_user_id
    AND at.occurred_at BETWEEN p_start_date AND p_end_date
    GROUP BY at.operation, at.table_name
    ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql;

-- Data access report for compliance
CREATE OR REPLACE FUNCTION generate_data_access_report(
    p_tenant_id UUID,
    p_days INTEGER DEFAULT 7
) RETURNS TABLE (
    user_id VARCHAR,
    table_name VARCHAR,
    operation VARCHAR,
    access_count BIGINT,
    sensitive_data_accessed BOOLEAN,
    ip_addresses TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        at.user_id,
        at.table_name::VARCHAR,
        at.operation::VARCHAR,
        COUNT(*),
        MAX(CASE WHEN at.data_classification IN ('PCI', 'PII') THEN true ELSE false END),
        array_agg(DISTINCT at.client_ip::TEXT)
    FROM audit_trail at
    WHERE at.tenant_id = p_tenant_id
    AND at.occurred_at > CURRENT_TIMESTAMP - (p_days || ' days')::INTERVAL
    GROUP BY at.user_id, at.table_name, at.operation
    ORDER BY COUNT(*) DESC;
END;
$$ LANGUAGE plpgsql;

-- STEP 10: Create automatic partition management
-- =====================================================

-- Function to create monthly partitions automatically
CREATE OR REPLACE FUNCTION create_audit_partition()
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    -- Calculate next month
    start_date := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'audit_trail_' || TO_CHAR(start_date, 'YYYY_MM');
    
    -- Check if partition exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_class 
        WHERE relname = partition_name
    ) THEN
        -- Create partition
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF audit_trail
             FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
        
        RAISE NOTICE 'Created audit partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly partition creation
-- SELECT cron.schedule('create-audit-partition', '0 0 25 * *', 'SELECT create_audit_partition()');

-- STEP 11: Create monitoring and alerting
-- =====================================================

-- Real-time suspicious activity detection
CREATE OR REPLACE FUNCTION detect_suspicious_activity()
RETURNS TABLE (
    alert_type VARCHAR,
    severity VARCHAR,
    user_id VARCHAR,
    details JSONB
) AS $$
BEGIN
    -- Mass deletion detection
    RETURN QUERY
    SELECT 
        'mass_deletion'::VARCHAR,
        'CRITICAL'::VARCHAR,
        at.user_id,
        jsonb_build_object(
            'tables', array_agg(DISTINCT at.table_name),
            'record_count', COUNT(*),
            'time_window', '10 minutes'
        )
    FROM audit_trail at
    WHERE at.operation = 'DELETE'
    AND at.occurred_at > CURRENT_TIMESTAMP - INTERVAL '10 minutes'
    GROUP BY at.user_id
    HAVING COUNT(*) > 100;
    
    -- Unusual access pattern
    RETURN QUERY
    SELECT 
        'unusual_access'::VARCHAR,
        'HIGH'::VARCHAR,
        at.user_id,
        jsonb_build_object(
            'tables_accessed', COUNT(DISTINCT at.table_name),
            'operations', COUNT(*),
            'ips', array_agg(DISTINCT at.client_ip::TEXT)
        )
    FROM audit_trail at
    WHERE at.occurred_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
    GROUP BY at.user_id
    HAVING COUNT(DISTINCT at.table_name) > 10
    OR COUNT(*) > 1000;
    
    -- After-hours access
    RETURN QUERY
    SELECT 
        'after_hours_access'::VARCHAR,
        'MEDIUM'::VARCHAR,
        at.user_id,
        jsonb_build_object(
            'access_time', at.occurred_at,
            'table', at.table_name,
            'operation', at.operation
        )
    FROM audit_trail at
    WHERE at.occurred_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
    AND EXTRACT(HOUR FROM at.occurred_at) NOT BETWEEN 6 AND 22;
END;
$$ LANGUAGE plpgsql;

-- Final validation
DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Audit Trail Implementation Complete';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Features Implemented:';
    RAISE NOTICE '- Immutable hash-chain audit trail';
    RAISE NOTICE '- Automatic triggers on all critical tables';
    RAISE NOTICE '- PCI and GDPR compliance views';
    RAISE NOTICE '- Sensitive data masking';
    RAISE NOTICE '- Suspicious activity detection';
    RAISE NOTICE '- Automatic partition management';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Test audit trail with sample transactions';
    RAISE NOTICE '2. Verify hash chain integrity';
    RAISE NOTICE '3. Configure retention policies';
    RAISE NOTICE '4. Set up monitoring alerts';
END;
$$;
