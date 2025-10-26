-- Complete Security Schema Migrations
-- Run this to set up all security components

-- ==================== USERS AND RBAC ====================

-- Users table with security fields
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    organization_id UUID NOT NULL,
    role VARCHAR(50) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    INDEX idx_email (email),
    INDEX idx_org (organization_id)
);

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'trial',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    UNIQUE(resource, action)
);

-- User-Role mapping
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    granted_by UUID,
    PRIMARY KEY (user_id, role_id)
);

-- Role-Permission mapping
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- ==================== PCI TOKENIZATION ====================

CREATE SCHEMA IF NOT EXISTS cde;

-- Tokenization vault
CREATE TABLE IF NOT EXISTS cde.tokenization_vault (
    token VARCHAR(32) PRIMARY KEY,
    encrypted_pan BYTEA NOT NULL,
    pan_hash VARCHAR(64) NOT NULL,
    masked_pan VARCHAR(19) NOT NULL,
    card_bin VARCHAR(6) NOT NULL,
    card_brand VARCHAR(20),
    expiry_month INTEGER,
    expiry_year INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ,
    access_count INTEGER DEFAULT 0,
    organization_id UUID,
    INDEX idx_pan_hash (pan_hash),
    INDEX idx_org_id (organization_id)
);

-- CDE access log
CREATE TABLE IF NOT EXISTS cde.access_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(32),
    action VARCHAR(20) NOT NULL,
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN,
    error_message TEXT,
    accessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== GDPR COMPLIANCE ====================

CREATE SCHEMA IF NOT EXISTS gdpr;

-- GDPR requests
CREATE TABLE IF NOT EXISTS gdpr.requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_type VARCHAR(20) NOT NULL,
    subject_id UUID NOT NULL,
    subject_email VARCHAR(255) NOT NULL,
    organization_id UUID,
    status VARCHAR(20) DEFAULT 'pending',
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    processed_by UUID,
    verification_token VARCHAR(64),
    verification_completed BOOLEAN DEFAULT FALSE,
    verification_expires_at TIMESTAMPTZ,
    reason TEXT,
    metadata JSONB,
    result JSONB
);

-- Data retention policies
CREATE TABLE IF NOT EXISTS gdpr.retention_policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_category VARCHAR(50) UNIQUE NOT NULL,
    retention_days INTEGER NOT NULL,
    legal_basis TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Consent records
CREATE TABLE IF NOT EXISTS gdpr.consent_records (
    consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL,
    purpose VARCHAR(100) NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    ip_address INET,
    user_agent TEXT
);

-- ==================== IMMUTABLE AUDIT TRAIL ====================

CREATE SCHEMA IF NOT EXISTS audit_immutable;

-- Immutable audit trail
CREATE TABLE IF NOT EXISTS audit_immutable.audit_trail (
    event_id UUID PRIMARY KEY,
    block_height BIGSERIAL UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    actor_id VARCHAR(100),
    actor_type VARCHAR(20),
    actor_ip INET,
    target_id VARCHAR(100),
    target_type VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    result VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB,
    event_hash VARCHAR(64) NOT NULL UNIQUE,
    previous_hash VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prevent modifications to audit trail
CREATE OR REPLACE FUNCTION audit_immutable.prevent_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit records are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS no_update ON audit_immutable.audit_trail;
CREATE TRIGGER no_update BEFORE UPDATE ON audit_immutable.audit_trail
FOR EACH ROW EXECUTE FUNCTION audit_immutable.prevent_modification();

DROP TRIGGER IF EXISTS no_delete ON audit_immutable.audit_trail;
CREATE TRIGGER no_delete BEFORE DELETE ON audit_immutable.audit_trail
FOR EACH ROW EXECUTE FUNCTION audit_immutable.prevent_modification();

-- ==================== KEY MANAGEMENT ====================

CREATE SCHEMA IF NOT EXISTS key_management;

-- Encryption keys table
CREATE TABLE IF NOT EXISTS key_management.encryption_keys (
    key_id UUID PRIMARY KEY,
    key_type VARCHAR(50) NOT NULL,
    key_version INTEGER NOT NULL,
    algorithm VARCHAR(50) NOT NULL,
    encrypted_key_material BYTEA NOT NULL,
    public_key TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    rotated_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL,
    metadata JSONB,
    UNIQUE(key_type, key_version)
);

-- Key rotation log
CREATE TABLE IF NOT EXISTS key_management.rotation_log (
    rotation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_type VARCHAR(50) NOT NULL,
    old_key_id UUID,
    new_key_id UUID,
    rotated_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_by VARCHAR(100),
    reason TEXT,
    success BOOLEAN,
    error_message TEXT
);

-- ==================== INITIAL DATA ====================

-- Insert default roles
INSERT INTO roles (name, description, is_system) VALUES
    ('billing_admin', 'Full administrative access to billing system', TRUE),
    ('billing_operator', 'Operational access for billing tasks', TRUE),
    ('billing_readonly', 'Read-only access to billing data', TRUE),
    ('billing_api', 'API access for external integrations', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions
INSERT INTO permissions (resource, action) VALUES
    ('billing', 'read'),
    ('billing', 'write'),
    ('billing', 'delete'),
    ('invoice', 'read'),
    ('invoice', 'write'),
    ('invoice', 'delete'),
    ('payment', 'read'),
    ('payment', 'process'),
    ('payment', 'refund'),
    ('user', 'read'),
    ('user', 'write'),
    ('user', 'delete'),
    ('admin', 'all'),
    ('pci', 'tokenize'),
    ('pci', 'detokenize'),
    ('gdpr', 'request'),
    ('gdpr', 'process'),
    ('audit', 'read'),
    ('audit', 'verify')
ON CONFLICT (resource, action) DO NOTHING;

-- Insert GDPR retention policies
INSERT INTO gdpr.retention_policies (data_category, retention_days, legal_basis) VALUES
    ('billing_data', 2555, 'Legal requirement - 7 years for tax purposes'),
    ('user_data', 1095, 'Legitimate interest - 3 years'),
    ('audit_logs', 2555, 'Legal requirement - 7 years for compliance'),
    ('payment_data', 2555, 'Legal requirement - PCI DSS and tax'),
    ('session_data', 90, 'Legitimate interest - 90 days')
ON CONFLICT (data_category) DO NOTHING;

-- ==================== GRANTS ====================

-- Create application role if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'billing_app') THEN
        CREATE ROLE billing_app WITH LOGIN PASSWORD 'changeme';
    END IF;
END
$$;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO billing_app;
GRANT ALL ON ALL TABLES IN SCHEMA public TO billing_app;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO billing_app;

GRANT USAGE ON SCHEMA cde TO billing_app;
GRANT SELECT, INSERT ON cde.tokenization_vault TO billing_app;
GRANT INSERT ON cde.access_log TO billing_app;

GRANT USAGE ON SCHEMA gdpr TO billing_app;
GRANT ALL ON ALL TABLES IN SCHEMA gdpr TO billing_app;

GRANT USAGE ON SCHEMA audit_immutable TO billing_app;
GRANT INSERT, SELECT ON audit_immutable.audit_trail TO billing_app;

GRANT USAGE ON SCHEMA key_management TO billing_app;
GRANT ALL ON ALL TABLES IN SCHEMA key_management TO billing_app;

-- ==================== INDEXES FOR PERFORMANCE ====================

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_immutable.audit_trail(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_immutable.audit_trail(actor_id);
CREATE INDEX IF NOT EXISTS idx_gdpr_subject ON gdpr.requests(subject_id);
CREATE INDEX IF NOT EXISTS idx_keys_type ON key_management.encryption_keys(key_type);

-- ==================== COMPLETION ====================

-- Verify installation
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM roles WHERE is_system = TRUE;
    RAISE NOTICE 'System roles created: %', v_count;
    
    SELECT COUNT(*) INTO v_count FROM permissions;
    RAISE NOTICE 'Permissions created: %', v_count;
    
    SELECT COUNT(*) INTO v_count FROM gdpr.retention_policies;
    RAISE NOTICE 'Retention policies created: %', v_count;
    
    RAISE NOTICE '✅ Security schema installation complete';
END
$$;
