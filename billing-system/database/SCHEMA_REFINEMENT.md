# Schema Refinement Analysis - ValueVerse Billing System

## Table Structure Optimization

### Current Schema Analysis

| Table | Rows Est. | Size | Bloat | Action Required |
|-------|-----------|------|-------|-----------------|
| usage_events | 1B+ | 450GB | 12% | Partition by month |
| invoices | 10M | 8GB | 5% | Normalize line_items |
| billing_transactions | 50M | 15GB | 8% | Archive old records |
| audit_trail | 500M | 120GB | 15% | Partition + compress |

### Column Definition Optimizations

```sql
-- Current inefficiencies and recommended fixes

-- 1. Optimize data types for space efficiency
ALTER TABLE usage_events 
ALTER COLUMN quantity TYPE NUMERIC(20,6);  -- From DECIMAL(20,8)

ALTER TABLE invoices
ALTER COLUMN total TYPE NUMERIC(12,2);     -- From DECIMAL(10,2) - support larger amounts

-- 2. Add compression for large text fields
ALTER TABLE audit_trail
ALTER COLUMN old_values SET STORAGE EXTERNAL,
ALTER COLUMN new_values SET STORAGE EXTERNAL;

-- 3. Use appropriate string lengths
ALTER TABLE organizations
ALTER COLUMN name TYPE VARCHAR(255),       -- From TEXT
ALTER COLUMN slug TYPE VARCHAR(100);       -- From TEXT

-- 4. Add ENUM types for better constraint
CREATE TYPE billing_status AS ENUM (
    'draft', 'open', 'paid', 'void', 'uncollectible', 'past_due'
);

ALTER TABLE invoices
ALTER COLUMN status TYPE billing_status
USING status::billing_status;

-- 5. Use domains for reusable constraints
CREATE DOMAIN email AS VARCHAR(255)
CHECK (VALUE ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$');

ALTER TABLE organizations
ALTER COLUMN billing_email TYPE email;
```

### Naming Convention Standardization

**Current Issues:**
- Inconsistent plural/singular (organizations vs subscription_plan)
- Mixed snake_case and camelCase in JSONB
- No prefix convention for views/functions

**Recommended Naming Standards:**

```sql
-- Table Naming: Plural, snake_case
RENAME TABLE subscription_plan TO subscription_plans;

-- Column Naming: Singular, snake_case
ALTER TABLE subscriptions 
RENAME COLUMN cancel_at_period_end TO is_cancel_at_period_end;

-- Index Naming: idx_<table>_<columns>_<type>
ALTER INDEX idx_usage_events_recent 
RENAME TO idx_usage_events_timestamp_partial;

-- Constraint Naming: <table>_<columns>_<type>
ALTER TABLE subscriptions
RENAME CONSTRAINT subscriptions_organization_id_fkey 
TO subscriptions_organization_id_fk;

-- Function Naming: fn_<action>_<entity>
CREATE OR REPLACE FUNCTION fn_calculate_invoice_total(
    invoice_id UUID
) RETURNS NUMERIC AS $$ ... $$;

-- View Naming: vw_<description>
CREATE OR REPLACE VIEW vw_active_subscriptions AS ...;

-- Materialized View: mv_<description>
CREATE MATERIALIZED VIEW mv_revenue_summary AS ...;
```

### Documentation Completeness

```sql
-- Add table and column comments
COMMENT ON TABLE organizations IS 
'Multi-tenant organizations - primary account entity';

COMMENT ON COLUMN organizations.slug IS 
'URL-safe unique identifier for public references';

COMMENT ON TABLE usage_events IS 
'Time-series data for usage tracking - partitioned by month';

COMMENT ON COLUMN usage_events.idempotency_key IS 
'Client-provided key for exactly-once processing';

-- Create documentation view
CREATE OR REPLACE VIEW vw_schema_documentation AS
SELECT 
    t.table_schema,
    t.table_name,
    obj_description(c.oid) as table_comment,
    col.column_name,
    col.data_type,
    col.is_nullable,
    col_description(c.oid, col.ordinal_position) as column_comment
FROM information_schema.tables t
JOIN pg_class c ON c.relname = t.table_name
JOIN information_schema.columns col ON col.table_name = t.table_name
WHERE t.table_schema = 'public'
ORDER BY t.table_name, col.ordinal_position;
```

## Schema Versioning Strategy

### Version Control System

```sql
-- Create schema versioning table
CREATE TABLE schema_versions (
    version_id SERIAL PRIMARY KEY,
    version_number VARCHAR(20) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    script_name VARCHAR(255) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    installed_by VARCHAR(100) NOT NULL DEFAULT CURRENT_USER,
    installed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    execution_time_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    rollback_script TEXT
);

-- Track current version
CREATE OR REPLACE FUNCTION fn_get_schema_version()
RETURNS VARCHAR AS $$
SELECT version_number 
FROM schema_versions 
WHERE success = TRUE 
ORDER BY version_id DESC 
LIMIT 1;
$$ LANGUAGE SQL;

-- Migration template
-- File: migrations/V2.1.0__add_subscription_items.sql
BEGIN;
-- Record migration start
INSERT INTO schema_versions (version_number, description, script_name)
VALUES ('2.1.0', 'Add subscription items table', 'V2.1.0__add_subscription_items.sql');

-- Migration logic
CREATE TABLE subscription_items (...);

-- Update version
UPDATE schema_versions 
SET success = TRUE, 
    execution_time_ms = EXTRACT(EPOCH FROM (NOW() - installed_at)) * 1000
WHERE version_number = '2.1.0';

COMMIT;
```

### Blue-Green Schema Deployment

```sql
-- Create shadow schema for zero-downtime migrations
CREATE SCHEMA billing_v2;

-- Copy current schema structure
SELECT fn_copy_schema('public', 'billing_v2');

-- Apply migrations to shadow schema
SET search_path TO billing_v2;
-- Run migrations...

-- Atomic schema swap
BEGIN;
ALTER SCHEMA public RENAME TO billing_old;
ALTER SCHEMA billing_v2 RENAME TO public;
COMMIT;

-- Cleanup after validation
DROP SCHEMA billing_old CASCADE;
```

## Table Partitioning Strategy

### Partition Large Tables

```sql
-- 1. Partition usage_events by month
CREATE TABLE usage_events_partitioned (
    LIKE usage_events INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create partitions
CREATE TABLE usage_events_2024_01 
PARTITION OF usage_events_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE usage_events_2024_02 
PARTITION OF usage_events_partitioned
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Automated partition creation
CREATE OR REPLACE FUNCTION fn_create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := DATE_TRUNC('month', NOW());
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'usage_events_' || TO_CHAR(start_date, 'YYYY_MM');
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF usage_events_partitioned
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly execution
CREATE EXTENSION IF NOT EXISTS pg_cron;
SELECT cron.schedule('create-partition', '0 0 25 * *', 
    'SELECT fn_create_monthly_partition()');
```

### Partition Maintenance

```sql
-- Drop old partitions
CREATE OR REPLACE FUNCTION fn_drop_old_partitions(
    retention_months INTEGER DEFAULT 12
) RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
BEGIN
    partition_date := DATE_TRUNC('month', NOW() - (retention_months || ' months')::INTERVAL);
    
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'usage_events_%'
        AND tablename < 'usage_events_' || TO_CHAR(partition_date, 'YYYY_MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I', partition_name);
        RAISE NOTICE 'Dropped partition: %', partition_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

## Schema Optimization Recommendations

### 1. Implement Computed Columns

```sql
-- Replace redundant storage with computed columns
ALTER TABLE invoices
ADD COLUMN days_overdue INTEGER 
GENERATED ALWAYS AS (
    CASE 
        WHEN status IN ('paid', 'void') THEN 0
        WHEN due_date < CURRENT_DATE THEN CURRENT_DATE - due_date
        ELSE 0
    END
) STORED;

ALTER TABLE subscriptions
ADD COLUMN days_until_renewal INTEGER
GENERATED ALWAYS AS (
    CASE
        WHEN status = 'active' THEN current_period_end::DATE - CURRENT_DATE
        ELSE NULL
    END
) STORED;
```

### 2. Implement Inheritance for Similar Tables

```sql
-- Base table for all financial transactions
CREATE TABLE financial_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Inherited tables
CREATE TABLE payment_transactions (
    payment_method_id UUID REFERENCES payment_methods(id),
    provider VARCHAR(50),
    provider_transaction_id VARCHAR(255)
) INHERITS (financial_transactions);

CREATE TABLE refund_transactions (
    original_transaction_id UUID REFERENCES payment_transactions(id),
    reason TEXT,
    initiated_by UUID
) INHERITS (financial_transactions);
```

### 3. JSON Schema Validation

```sql
-- Add CHECK constraints for JSONB columns
ALTER TABLE usage_events
ADD CONSTRAINT check_properties_schema CHECK (
    jsonb_typeof(properties) = 'object' AND
    properties ? 'source' AND
    jsonb_typeof(properties->'source') = 'string'
);

-- Create validation function
CREATE OR REPLACE FUNCTION fn_validate_invoice_metadata(metadata JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Required fields
    IF NOT (metadata ? 'tax_id' AND metadata ? 'billing_period') THEN
        RETURN FALSE;
    END IF;
    
    -- Type validation
    IF jsonb_typeof(metadata->'tax_id') != 'string' OR
       jsonb_typeof(metadata->'billing_period') != 'object' THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

ALTER TABLE invoices
ADD CONSTRAINT check_metadata_valid 
CHECK (fn_validate_invoice_metadata(metadata));
```

## Maintenance and Scalability Improvements

### 1. Automated Maintenance Tasks

```sql
-- Vacuum and analyze automation
CREATE OR REPLACE FUNCTION fn_auto_maintenance()
RETURNS void AS $$
BEGIN
    -- Vacuum analyze high-churn tables
    EXECUTE 'VACUUM ANALYZE usage_events';
    EXECUTE 'VACUUM ANALYZE billing_transactions';
    
    -- Reindex if needed
    EXECUTE 'REINDEX TABLE CONCURRENTLY usage_events';
    
    -- Update statistics
    EXECUTE 'ANALYZE';
END;
$$ LANGUAGE plpgsql;

-- Schedule weekly
SELECT cron.schedule('auto-maintenance', '0 2 * * 0', 
    'SELECT fn_auto_maintenance()');
```

### 2. Schema Health Monitoring

```sql
CREATE OR REPLACE VIEW vw_schema_health AS
SELECT 
    'Table Bloat' as metric,
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    ROUND(
        CASE WHEN pg_total_relation_size(schemaname||'.'||tablename) > 0
        THEN 100.0 * (pg_total_relation_size(schemaname||'.'||tablename) - 
                      pg_relation_size(schemaname||'.'||tablename)) / 
                      pg_total_relation_size(schemaname||'.'||tablename)
        ELSE 0 END, 2
    ) as bloat_percent
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Implementation Priority Matrix

| Task | Impact | Effort | Priority | Timeline |
|------|--------|--------|----------|----------|
| Add ENUM types | Medium | Low | High | Week 1 |
| Partition usage_events | High | Medium | High | Week 1 |
| Normalize invoice_line_items | High | Medium | High | Week 2 |
| Implement computed columns | Medium | Low | Medium | Week 2 |
| Add schema versioning | High | Medium | High | Week 2 |
| JSON schema validation | Medium | Medium | Medium | Week 3 |
| Setup auto-maintenance | High | Low | High | Week 3 |
| Implement inheritance | Low | High | Low | Month 2 |
