-- Supabase Database Setup for ValueVerse Platform
-- Run this in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- ==================== TABLES ====================

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'analyst', 'sales', 'csm', 'viewer')),
    organization_id UUID,
    expertise_level TEXT DEFAULT 'intermediate' CHECK (expertise_level IN ('beginner', 'intermediate', 'expert')),
    preferences JSONB DEFAULT '{"theme": "light", "dataGranularity": "summary", "showFormulas": false, "enableNotifications": true}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Organizations/Tenants table
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    subdomain TEXT UNIQUE NOT NULL,
    plan TEXT DEFAULT 'starter' CHECK (plan IN ('starter', 'professional', 'enterprise')),
    industry TEXT,
    company_size TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'trial')),
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Value Models table
CREATE TABLE IF NOT EXISTS public.value_models (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    industry TEXT,
    stage TEXT,
    inputs JSONB NOT NULL,
    results JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    version INTEGER DEFAULT 1,
    is_published BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Value Strategies table
CREATE TABLE IF NOT EXISTS public.value_strategies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    model_id UUID REFERENCES public.value_models(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    target_value DECIMAL(15, 2),
    timeline_days INTEGER,
    milestones JSONB DEFAULT '[]'::jsonb,
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Execution Tasks table
CREATE TABLE IF NOT EXISTS public.execution_tasks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    strategy_id UUID REFERENCES public.value_strategies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES public.profiles(id),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'paused')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    notes TEXT,
    blockers TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Shared Links table
CREATE TABLE IF NOT EXISTS public.shared_links (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    model_id UUID REFERENCES public.value_models(id) ON DELETE CASCADE,
    short_code TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    views INTEGER DEFAULT 0,
    max_views INTEGER,
    password_hash TEXT,
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log table
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id),
    organization_id UUID REFERENCES public.organizations(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================== INDEXES ====================

CREATE INDEX idx_profiles_organization ON public.profiles(organization_id);
CREATE INDEX idx_profiles_role ON public.profiles(role);
CREATE INDEX idx_value_models_user ON public.value_models(user_id);
CREATE INDEX idx_value_models_organization ON public.value_models(organization_id);
CREATE INDEX idx_value_strategies_model ON public.value_strategies(model_id);
CREATE INDEX idx_execution_tasks_strategy ON public.execution_tasks(strategy_id);
CREATE INDEX idx_execution_tasks_assigned ON public.execution_tasks(assigned_to);
CREATE INDEX idx_execution_tasks_status ON public.execution_tasks(status);
CREATE INDEX idx_shared_links_short_code ON public.shared_links(short_code);
CREATE INDEX idx_audit_logs_user ON public.audit_logs(user_id);
CREATE INDEX idx_audit_logs_organization ON public.audit_logs(organization_id);
CREATE INDEX idx_audit_logs_created ON public.audit_logs(created_at);

-- ==================== ROW LEVEL SECURITY ====================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.value_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.value_strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.execution_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shared_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view their own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Organizations policies
CREATE POLICY "Organization members can view their org" ON public.organizations
    FOR SELECT USING (
        id IN (
            SELECT organization_id FROM public.profiles WHERE id = auth.uid()
        )
    );

-- Value Models policies
CREATE POLICY "Users can view their own models" ON public.value_models
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create models" ON public.value_models
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own models" ON public.value_models
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own models" ON public.value_models
    FOR DELETE USING (user_id = auth.uid());

-- Organization members can view org models
CREATE POLICY "Org members can view org models" ON public.value_models
    FOR SELECT USING (
        organization_id IN (
            SELECT organization_id FROM public.profiles WHERE id = auth.uid()
        )
    );

-- ==================== FUNCTIONS ====================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON public.organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_value_models_updated_at BEFORE UPDATE ON public.value_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_value_strategies_updated_at BEFORE UPDATE ON public.value_strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_execution_tasks_updated_at BEFORE UPDATE ON public.execution_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to handle new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user creation
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==================== INITIAL DATA ====================

-- Create default organization
INSERT INTO public.organizations (id, name, subdomain, plan, status)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'Demo Organization',
    'demo',
    'enterprise',
    'active'
) ON CONFLICT (subdomain) DO NOTHING;

-- ==================== GRANTS ====================

-- Grant necessary permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
