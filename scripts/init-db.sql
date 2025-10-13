-- ============================================================================
-- ValueVerse Platform - Database Initialization Script
-- ============================================================================

-- Create database if not exists
SELECT 'CREATE DATABASE valueverse'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'valueverse')\gexec

-- Connect to valueverse database
\c valueverse;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- COMPANIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    size VARCHAR(50),
    description TEXT,
    website VARCHAR(255),
    logo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- VALUE MODELS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS value_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    status VARCHAR(50) DEFAULT 'draft',
    total_potential_value DECIMAL(15, 2),
    confidence_score DECIMAL(3, 2),
    implementation_timeline INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- VALUE DRIVERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS value_drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    value_model_id UUID REFERENCES value_models(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    impact_area VARCHAR(100),
    potential_value DECIMAL(15, 2),
    effort_required VARCHAR(50),
    time_to_value INTEGER,
    confidence DECIMAL(3, 2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- COMMITMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS commitments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    value_model_id UUID REFERENCES value_models(id),
    company_id UUID REFERENCES companies(id),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_value DECIMAL(15, 2),
    committed_value DECIMAL(15, 2),
    status VARCHAR(50) DEFAULT 'pending',
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MILESTONES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commitment_id UUID REFERENCES commitments(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_date DATE,
    completion_date DATE,
    target_value DECIMAL(15, 2),
    actual_value DECIMAL(15, 2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- EXECUTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commitment_id UUID REFERENCES commitments(id),
    milestone_id UUID REFERENCES milestones(id),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'in_progress',
    progress_percentage INTEGER DEFAULT 0,
    value_delivered DECIMAL(15, 2),
    blockers TEXT,
    next_steps TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AMPLIFICATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS amplifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES executions(id),
    company_id UUID REFERENCES companies(id),
    user_id UUID REFERENCES users(id),
    type VARCHAR(50),  -- 'success_story', 'case_study', 'reference', 'testimonial'
    title VARCHAR(255) NOT NULL,
    content TEXT,
    impact_summary TEXT,
    metrics JSONB,
    visibility VARCHAR(50) DEFAULT 'internal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- NOTIFICATIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB,
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUDIT LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    entity_type VARCHAR(100),
    entity_id UUID,
    action VARCHAR(50),
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- API KEYS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- Company indexes
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);

-- Value model indexes
CREATE INDEX IF NOT EXISTS idx_value_models_company_id ON value_models(company_id);
CREATE INDEX IF NOT EXISTS idx_value_models_user_id ON value_models(user_id);
CREATE INDEX IF NOT EXISTS idx_value_models_status ON value_models(status);
CREATE INDEX IF NOT EXISTS idx_value_models_created_at ON value_models(created_at DESC);

-- Value driver indexes
CREATE INDEX IF NOT EXISTS idx_value_drivers_model_id ON value_drivers(value_model_id);
CREATE INDEX IF NOT EXISTS idx_value_drivers_category ON value_drivers(category);

-- Commitment indexes
CREATE INDEX IF NOT EXISTS idx_commitments_company_id ON commitments(company_id);
CREATE INDEX IF NOT EXISTS idx_commitments_user_id ON commitments(user_id);
CREATE INDEX IF NOT EXISTS idx_commitments_status ON commitments(status);

-- Milestone indexes
CREATE INDEX IF NOT EXISTS idx_milestones_commitment_id ON milestones(commitment_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON milestones(status);
CREATE INDEX IF NOT EXISTS idx_milestones_target_date ON milestones(target_date);

-- Execution indexes
CREATE INDEX IF NOT EXISTS idx_executions_commitment_id ON executions(commitment_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);

-- Amplification indexes
CREATE INDEX IF NOT EXISTS idx_amplifications_company_id ON amplifications(company_id);
CREATE INDEX IF NOT EXISTS idx_amplifications_type ON amplifications(type);

-- Notification indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Session indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_value_models_updated_at BEFORE UPDATE ON value_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_value_drivers_updated_at BEFORE UPDATE ON value_drivers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_commitments_updated_at BEFORE UPDATE ON commitments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_milestones_updated_at BEFORE UPDATE ON milestones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_executions_updated_at BEFORE UPDATE ON executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_amplifications_updated_at BEFORE UPDATE ON amplifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- DEFAULT ADMIN USER
-- ============================================================================

-- Create admin user with hashed password (password: admin123)
-- Note: In production, use proper password hashing
INSERT INTO users (email, name, password_hash, role, is_active, email_verified)
VALUES (
    'admin@valueverse.ai',
    'Admin User',
    crypt('admin123', gen_salt('bf')),
    'admin',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- PERMISSIONS AND SECURITY
-- ============================================================================

-- Create application role
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'valueverse_app') THEN
        CREATE ROLE valueverse_app WITH LOGIN PASSWORD 'app_password';
    END IF;
END $$;

-- Grant permissions
GRANT CONNECT ON DATABASE valueverse TO valueverse_app;
GRANT USAGE ON SCHEMA public TO valueverse_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO valueverse_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO valueverse_app;

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
END $$;
