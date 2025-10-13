-- ValueVerse Platform - Living Value Graph Database Schema
-- PostgreSQL 15+ with pgvector extension for AI embeddings

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- MULTI-TENANCY FOUNDATION
-- =====================================================

-- Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    domain VARCHAR(255),
    logo_url TEXT,
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('pending', 'active', 'suspended', 'deleted')),
    settings JSONB DEFAULT '{}',
    subscription JSONB DEFAULT '{}',
    limits JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX idx_tenants_status ON tenants(status);

-- Users table with tenant context
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    role_id UUID,
    department VARCHAR(100),
    title VARCHAR(100),
    phone VARCHAR(50),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
    email_verified BOOLEAN DEFAULT FALSE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(tenant_id, status);

-- =====================================================
-- LIVING VALUE GRAPH CORE
-- =====================================================

-- Value Models - The core value tracking entity
CREATE TABLE value_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    stage VARCHAR(50) DEFAULT 'hypothesis' CHECK (stage IN ('hypothesis', 'commitment', 'execution', 'realization', 'amplification')),
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    
    -- Value metrics
    target_value DECIMAL(15, 2),
    realized_value DECIMAL(15, 2) DEFAULT 0,
    confidence_score DECIMAL(3, 2) DEFAULT 0.5,
    
    -- Temporal tracking
    hypothesis_date DATE,
    commitment_date DATE,
    start_date DATE,
    target_date DATE,
    realized_date DATE,
    
    -- Graph connections
    parent_model_id UUID REFERENCES value_models(id),
    
    -- AI embeddings for similarity search
    embedding vector(1536),
    
    -- Flexible data storage
    hypothesis JSONB DEFAULT '{}',
    commitment JSONB DEFAULT '{}',
    execution_data JSONB DEFAULT '{}',
    realization_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_value_models_tenant_id ON value_models(tenant_id);
CREATE INDEX idx_value_models_stage ON value_models(tenant_id, stage);
CREATE INDEX idx_value_models_status ON value_models(tenant_id, status);

-- Value Drivers - Components that drive value
CREATE TABLE value_drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    value_model_id UUID NOT NULL REFERENCES value_models(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    
    -- Metrics
    baseline_value DECIMAL(15, 2),
    target_value DECIMAL(15, 2),
    current_value DECIMAL(15, 2),
    unit VARCHAR(50),
    
    -- Impact analysis
    impact_score DECIMAL(3, 2),
    confidence_level DECIMAL(3, 2),
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_value_drivers_tenant_id ON value_drivers(tenant_id);
CREATE INDEX idx_value_drivers_model_id ON value_drivers(value_model_id);

-- =====================================================
-- AGENT SYSTEM
-- =====================================================

-- Agent Conversations
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    value_model_id UUID REFERENCES value_models(id),
    
    -- Conversation metadata
    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'archived')),
    
    -- Agent tracking
    current_agent VARCHAR(50),
    agent_handoffs JSONB DEFAULT '[]',
    
    -- Context and memory
    context JSONB DEFAULT '{}',
    memory_snapshot JSONB DEFAULT '{}',
    
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_conversations_tenant_id ON agent_conversations(tenant_id);
CREATE INDEX idx_agent_conversations_user_id ON agent_conversations(user_id);

-- Agent Messages
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    
    -- Message details
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'function')),
    agent_name VARCHAR(50),
    content TEXT NOT NULL,
    
    -- Thinking and reasoning
    thought_process JSONB DEFAULT '{}',
    confidence_score DECIMAL(3, 2),
    
    -- Artifacts generated
    artifacts JSONB DEFAULT '[]',
    
    -- Embeddings for semantic search
    embedding vector(1536),
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_messages_tenant_id ON agent_messages(tenant_id);
CREATE INDEX idx_agent_messages_conversation_id ON agent_messages(conversation_id);

-- =====================================================
-- FUNCTIONS & TRIGGERS
-- =====================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables with updated_at
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_value_models_updated_at BEFORE UPDATE ON value_models 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_conversations_updated_at BEFORE UPDATE ON agent_conversations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row-level security policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE value_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_conversations ENABLE ROW LEVEL SECURITY;

-- Create policies for tenant isolation
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

CREATE POLICY tenant_isolation_value_models ON value_models
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

CREATE POLICY tenant_isolation_conversations ON agent_conversations
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
