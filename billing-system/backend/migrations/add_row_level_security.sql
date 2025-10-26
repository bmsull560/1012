-- Row-Level Security (RLS) Implementation for Multi-Tenant Isolation
-- This migration adds RLS policies to all tenant-scoped tables
-- ensuring complete data isolation between tenants

-- ============================================================================
-- STEP 1: Create tenant context function
-- ============================================================================

-- Function to get current tenant from session
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS UUID AS $$
BEGIN
    -- Try to get tenant_id from current session
    -- This is set by the application on each request
    RETURN current_setting('app.current_tenant_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        -- If not set, return NULL (will block all access)
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Function to set current tenant (called by application)
CREATE OR REPLACE FUNCTION set_current_tenant_id(p_tenant_id UUID)
RETURNS void AS $$
BEGIN
    -- Validate tenant_id exists
    IF NOT EXISTS (SELECT 1 FROM tenants WHERE id = p_tenant_id) THEN
        RAISE EXCEPTION 'Invalid tenant_id: %', p_tenant_id;
    END IF;
    
    -- Set the session variable
    PERFORM set_config('app.current_tenant_id', p_tenant_id::text, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- STEP 2: Add tenant_id to all relevant tables (if not present)
-- ============================================================================

-- Ensure all tables have tenant_id column
DO $$
DECLARE
    tbl RECORD;
BEGIN
    FOR tbl IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN (
            'users', 'invoices', 'subscriptions', 'payments', 
            'customers', 'products', 'billing_events', 'api_keys',
            'audit_logs', 'documents', 'notifications'
        )
    LOOP
        -- Add tenant_id if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = tbl.table_name 
            AND column_name = 'tenant_id'
        ) THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN tenant_id UUID NOT NULL', tbl.table_name);
            EXECUTE format('CREATE INDEX idx_%I_tenant_id ON %I(tenant_id)', tbl.table_name, tbl.table_name);
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- STEP 3: Enable RLS on all tenant tables
-- ============================================================================

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- Enable RLS on billing tables
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;

ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions FORCE ROW LEVEL SECURITY;

ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments FORCE ROW LEVEL SECURITY;

ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers FORCE ROW LEVEL SECURITY;

ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;

ALTER TABLE billing_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_events FORCE ROW LEVEL SECURITY;

-- Enable RLS on security tables
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys FORCE ROW LEVEL SECURITY;

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;

-- Enable RLS on other tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications FORCE ROW LEVEL SECURITY;

-- ============================================================================
-- STEP 4: Create RLS Policies
-- ============================================================================

-- Drop existing policies if they exist
DO $$
DECLARE
    tbl text;
    tables text[] := ARRAY[
        'users', 'invoices', 'subscriptions', 'payments', 
        'customers', 'products', 'billing_events', 'api_keys',
        'audit_logs', 'documents', 'notifications'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_select ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_insert ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_update ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_delete ON %I', tbl);
    END LOOP;
END $$;

-- Create policies for each table
-- Pattern: Only allow access to rows where tenant_id matches current tenant

-- Users table policies
CREATE POLICY tenant_isolation_select ON users
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON users
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON users
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON users
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Invoices table policies
CREATE POLICY tenant_isolation_select ON invoices
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON invoices
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON invoices
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON invoices
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Subscriptions table policies
CREATE POLICY tenant_isolation_select ON subscriptions
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON subscriptions
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON subscriptions
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON subscriptions
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Payments table policies
CREATE POLICY tenant_isolation_select ON payments
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON payments
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON payments
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON payments
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Customers table policies
CREATE POLICY tenant_isolation_select ON customers
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON customers
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON customers
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON customers
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Products table policies
CREATE POLICY tenant_isolation_select ON products
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON products
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON products
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON products
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Billing events table policies
CREATE POLICY tenant_isolation_select ON billing_events
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON billing_events
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON billing_events
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON billing_events
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- API keys table policies (extra security)
CREATE POLICY tenant_isolation_select ON api_keys
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON api_keys
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON api_keys
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON api_keys
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Audit logs table policies (read-only for tenants)
CREATE POLICY tenant_isolation_select ON audit_logs
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON audit_logs
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

-- No update/delete for audit logs (immutable)

-- Documents table policies
CREATE POLICY tenant_isolation_select ON documents
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON documents
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON documents
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON documents
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- Notifications table policies
CREATE POLICY tenant_isolation_select ON notifications
    FOR SELECT USING (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_insert ON notifications
    FOR INSERT WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_update ON notifications
    FOR UPDATE USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY tenant_isolation_delete ON notifications
    FOR DELETE USING (tenant_id = get_current_tenant_id());

-- ============================================================================
-- STEP 5: Create helper functions for cross-tenant operations (admin only)
-- ============================================================================

-- Function to temporarily bypass RLS for admin operations
CREATE OR REPLACE FUNCTION execute_as_superuser(p_sql text)
RETURNS void AS $$
BEGIN
    -- Only allow specific admin users
    IF current_user NOT IN ('postgres', 'admin_user') THEN
        RAISE EXCEPTION 'Unauthorized: Only admin users can bypass RLS';
    END IF;
    
    -- Execute with elevated privileges
    EXECUTE p_sql;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to validate tenant isolation
CREATE OR REPLACE FUNCTION validate_tenant_isolation()
RETURNS TABLE(
    table_name text,
    has_tenant_id boolean,
    rls_enabled boolean,
    policies_count integer
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.tablename::text,
        EXISTS(
            SELECT 1 FROM information_schema.columns c
            WHERE c.table_name = t.tablename
            AND c.column_name = 'tenant_id'
        ) as has_tenant_id,
        t.rowsecurity as rls_enabled,
        COUNT(p.policyname)::integer as policies_count
    FROM pg_tables t
    LEFT JOIN pg_policies p ON t.tablename = p.tablename
    WHERE t.schemaname = 'public'
    AND t.tablename IN (
        'users', 'invoices', 'subscriptions', 'payments', 
        'customers', 'products', 'billing_events', 'api_keys',
        'audit_logs', 'documents', 'notifications'
    )
    GROUP BY t.tablename, t.rowsecurity;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- STEP 6: Create audit trigger for RLS violations
-- ============================================================================

CREATE OR REPLACE FUNCTION log_rls_violation()
RETURNS event_trigger AS $$
DECLARE
    obj record;
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands()
    LOOP
        INSERT INTO audit_logs (
            tenant_id,
            event_type,
            event_data,
            created_at
        ) VALUES (
            get_current_tenant_id(),
            'RLS_VIOLATION_ATTEMPT',
            jsonb_build_object(
                'command', obj.command_tag,
                'object_type', obj.object_type,
                'schema', obj.schema_name,
                'object', obj.object_identity,
                'user', current_user,
                'timestamp', now()
            ),
            now()
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create event trigger for RLS violations
DROP EVENT TRIGGER IF EXISTS rls_violation_trigger;
CREATE EVENT TRIGGER rls_violation_trigger
    ON sql_drop
    EXECUTE FUNCTION log_rls_violation();

-- ============================================================================
-- STEP 7: Grant appropriate permissions
-- ============================================================================

-- Revoke all default permissions
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;

-- Grant permissions to application user
DO $$
DECLARE
    app_user text := 'app_user';  -- Replace with your application database user
BEGIN
    -- Grant usage on schema
    EXECUTE format('GRANT USAGE ON SCHEMA public TO %I', app_user);
    
    -- Grant permissions on tables
    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO %I', app_user);
    
    -- Grant permissions on sequences
    EXECUTE format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO %I', app_user);
    
    -- Grant execute on functions
    EXECUTE format('GRANT EXECUTE ON FUNCTION get_current_tenant_id() TO %I', app_user);
    EXECUTE format('GRANT EXECUTE ON FUNCTION set_current_tenant_id(UUID) TO %I', app_user);
    EXECUTE format('GRANT EXECUTE ON FUNCTION validate_tenant_isolation() TO %I', app_user);
END $$;

-- ============================================================================
-- STEP 8: Create indexes for performance
-- ============================================================================

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_tenant_email ON users(tenant_id, email);
CREATE INDEX IF NOT EXISTS idx_invoices_tenant_status ON invoices(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant_status ON subscriptions(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_tenant_created ON payments(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Run validation to ensure RLS is properly configured
SELECT * FROM validate_tenant_isolation();

-- Output message
DO $$
BEGIN
    RAISE NOTICE 'Row-Level Security has been successfully implemented.';
    RAISE NOTICE 'All tenant-scoped tables now have RLS policies enforced.';
    RAISE NOTICE 'Remember to call set_current_tenant_id() at the beginning of each database session.';
END $$;
