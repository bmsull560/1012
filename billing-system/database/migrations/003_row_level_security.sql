-- =====================================================
-- Row-Level Security Implementation
-- Execution Time: ~3 days
-- Priority: CRITICAL
-- =====================================================

-- STEP 1: Create tenant context management functions
-- =====================================================

-- Function to set current tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_id::TEXT, false);
    PERFORM set_config('app.current_user', current_user, false);
    PERFORM set_config('app.request_time', now()::TEXT, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current tenant context
CREATE OR REPLACE FUNCTION get_tenant_context()
RETURNS UUID AS $$
    SELECT NULLIF(current_setting('app.current_tenant', true), '')::UUID;
$$ LANGUAGE SQL STABLE;

-- Function to verify tenant access
CREATE OR REPLACE FUNCTION verify_tenant_access(tenant_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if user has access to this tenant
    IF get_tenant_context() IS NULL THEN
        RETURN FALSE;
    END IF;
    
    IF get_tenant_context() != tenant_id THEN
        -- Log unauthorized access attempt
        INSERT INTO security_audit_log (
            event_type, user_id, tenant_id, details, timestamp
        ) VALUES (
            'unauthorized_access_attempt',
            current_user,
            tenant_id,
            jsonb_build_object('requested_tenant', tenant_id, 'current_tenant', get_tenant_context()),
            now()
        );
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- STEP 2: Enable RLS on all tenant-scoped tables
-- =====================================================

-- Enable RLS on organizations table
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Enable RLS on core business tables
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_methods ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE pricing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_limits ENABLE ROW LEVEL SECURITY;

-- STEP 3: Create RLS Policies
-- =====================================================

-- Organizations table policies
DROP POLICY IF EXISTS tenant_isolation_policy ON organizations;
CREATE POLICY tenant_isolation_policy ON organizations
    FOR ALL
    USING (id = get_tenant_context())
    WITH CHECK (id = get_tenant_context());

-- Grant bypass for superusers
DROP POLICY IF EXISTS superuser_bypass ON organizations;
CREATE POLICY superuser_bypass ON organizations
    FOR ALL
    USING (current_user IN ('postgres', 'billing_admin'))
    WITH CHECK (current_user IN ('postgres', 'billing_admin'));

-- Subscriptions table policies
DROP POLICY IF EXISTS tenant_isolation_policy ON subscriptions;
CREATE POLICY tenant_isolation_policy ON subscriptions
    FOR ALL
    USING (organization_id = get_tenant_context())
    WITH CHECK (organization_id = get_tenant_context());

-- Usage events table policies
DROP POLICY IF EXISTS tenant_isolation_policy ON usage_events;
CREATE POLICY tenant_isolation_policy ON usage_events
    FOR ALL
    USING (organization_id = get_tenant_context())
    WITH CHECK (organization_id = get_tenant_context());

-- Invoices table policies
DROP POLICY IF EXISTS tenant_isolation_policy ON invoices;
CREATE POLICY tenant_isolation_policy ON invoices
    FOR ALL
    USING (organization_id = get_tenant_context())
    WITH CHECK (organization_id = get_tenant_context());

-- Payment methods table policies
DROP POLICY IF EXISTS tenant_isolation_policy ON payment_methods;
CREATE POLICY tenant_isolation_policy ON payment_methods
    FOR ALL
    USING (organization_id = get_tenant_context())
    WITH CHECK (organization_id = get_tenant_context());

-- Billing transactions table policies
DROP POLICY IF EXISTS tenant_isolation_policy ON billing_transactions;
CREATE POLICY tenant_isolation_policy ON billing_transactions
    FOR ALL
    USING (organization_id = get_tenant_context())
    WITH CHECK (organization_id = get_tenant_context());

-- Usage limits table policies
DROP POLICY IF EXISTS tenant_isolation_policy ON usage_limits;
CREATE POLICY tenant_isolation_policy ON usage_limits
    FOR ALL
    USING (
        subscription_id IN (
            SELECT id FROM subscriptions 
            WHERE organization_id = get_tenant_context()
        )
    );

-- Pricing rules (read-only for tenants)
DROP POLICY IF EXISTS tenant_read_policy ON pricing_rules;
CREATE POLICY tenant_read_policy ON pricing_rules
    FOR SELECT
    USING (
        plan_id IN (
            SELECT plan_id FROM subscriptions 
            WHERE organization_id = get_tenant_context()
        )
        OR is_public = true
    );

-- STEP 4: Create security audit table
-- =====================================================

CREATE TABLE IF NOT EXISTS security_audit_log (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    tenant_id UUID,
    ip_address INET DEFAULT inet_client_addr(),
    details JSONB,
    timestamp TIMESTAMP DEFAULT now(),
    session_id VARCHAR(100) DEFAULT current_setting('app.session_id', true)
);

CREATE INDEX idx_security_audit_timestamp ON security_audit_log(timestamp DESC);
CREATE INDEX idx_security_audit_tenant ON security_audit_log(tenant_id, timestamp DESC);
CREATE INDEX idx_security_audit_event ON security_audit_log(event_type, timestamp DESC);

-- STEP 5: Create helper functions for application
-- =====================================================

-- Function to execute queries with tenant context
CREATE OR REPLACE FUNCTION execute_as_tenant(
    tenant_id UUID,
    query_text TEXT
) RETURNS SETOF RECORD AS $$
BEGIN
    -- Set tenant context
    PERFORM set_tenant_context(tenant_id);
    
    -- Log query execution
    INSERT INTO security_audit_log (event_type, tenant_id, details)
    VALUES ('tenant_query_execution', tenant_id, jsonb_build_object('query', query_text));
    
    -- Execute query
    RETURN QUERY EXECUTE query_text;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check RLS status
CREATE OR REPLACE FUNCTION check_rls_status()
RETURNS TABLE (
    table_name TEXT,
    rls_enabled BOOLEAN,
    policies_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.relname::TEXT,
        c.relrowsecurity,
        COUNT(p.polname)::INTEGER
    FROM pg_class c
    LEFT JOIN pg_policy p ON c.oid = p.polrelid
    WHERE c.relkind = 'r'
    AND c.relnamespace = 'public'::regnamespace
    GROUP BY c.relname, c.relrowsecurity
    ORDER BY c.relname;
END;
$$ LANGUAGE plpgsql;

-- STEP 6: Create application user roles with RLS
-- =====================================================

-- Create application role
CREATE ROLE app_user LOGIN;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
GRANT EXECUTE ON FUNCTION set_tenant_context(UUID) TO app_user;
GRANT EXECUTE ON FUNCTION get_tenant_context() TO app_user;

-- Create read-only role
CREATE ROLE app_readonly LOGIN;
GRANT USAGE ON SCHEMA public TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;
GRANT EXECUTE ON FUNCTION set_tenant_context(UUID) TO app_readonly;
GRANT EXECUTE ON FUNCTION get_tenant_context() TO app_readonly;

-- STEP 7: Validation queries
-- =====================================================

-- Validate RLS is working
DO $$
DECLARE
    test_tenant_id UUID := '00000000-0000-0000-0000-000000000001';
    record_count INTEGER;
BEGIN
    -- Set a test tenant context
    PERFORM set_tenant_context(test_tenant_id);
    
    -- Try to query organizations
    SELECT COUNT(*) INTO record_count 
    FROM organizations;
    
    -- Check if RLS is filtering correctly
    IF record_count > 1 THEN
        RAISE WARNING 'RLS may not be working correctly. Multiple organizations visible.';
    END IF;
    
    -- Clear context
    PERFORM set_config('app.current_tenant', '', false);
    
    RAISE NOTICE 'RLS validation complete';
END;
$$;

-- Create monitoring view for RLS violations
CREATE OR REPLACE VIEW vw_rls_violations AS
SELECT 
    event_type,
    user_id,
    tenant_id,
    ip_address,
    details,
    timestamp
FROM security_audit_log
WHERE event_type IN ('unauthorized_access_attempt', 'rls_violation')
AND timestamp > now() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- STEP 8: Add RLS bypass for maintenance
-- =====================================================

-- Create maintenance function that bypasses RLS
CREATE OR REPLACE FUNCTION maintenance_bypass_rls(
    maintenance_key TEXT,
    query_text TEXT
) RETURNS SETOF RECORD AS $$
BEGIN
    -- Verify maintenance key
    IF maintenance_key != current_setting('app.maintenance_key', true) THEN
        RAISE EXCEPTION 'Invalid maintenance key';
    END IF;
    
    -- Log maintenance action
    INSERT INTO security_audit_log (event_type, user_id, details)
    VALUES ('maintenance_rls_bypass', current_user, jsonb_build_object('query', query_text));
    
    -- Execute with superuser privileges
    SET LOCAL row_security = OFF;
    RETURN QUERY EXECUTE query_text;
    RESET row_security;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute only to maintenance role
REVOKE ALL ON FUNCTION maintenance_bypass_rls(TEXT, TEXT) FROM PUBLIC;
CREATE ROLE maintenance_user;
GRANT EXECUTE ON FUNCTION maintenance_bypass_rls(TEXT, TEXT) TO maintenance_user;

-- Final message
DO $$
BEGIN
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Row-Level Security Implementation Complete';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Update application to call set_tenant_context()';
    RAISE NOTICE '2. Test with different tenant contexts';
    RAISE NOTICE '3. Monitor vw_rls_violations for issues';
    RAISE NOTICE '4. Review security_audit_log regularly';
END;
$$;
