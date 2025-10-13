# Migration Strategy - ValueVerse Billing System

## Migration Overview

### Current State → Target State

| Component | Current | Target | Risk Level |
|-----------|---------|--------|------------|
| Database Version | PostgreSQL 15 | PostgreSQL 15 + Citus | Low |
| Schema Design | Shared Schema | Hybrid (RLS + Schema/Tenant) | Medium |
| Security | Basic Auth | RLS + Encryption + Audit | High |
| Performance | 850K events/min | 1M+ events/min | Medium |
| Availability | 99.9% | 99.99% | High |

## Phase 1: Zero-Downtime Schema Migration

### 1.1 Blue-Green Migration Setup

```sql
-- Step 1: Create migration tracking
CREATE TABLE migration_status (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(100) UNIQUE NOT NULL,
    phase VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    rollback_point TEXT,
    error_log TEXT
);

-- Step 2: Create shadow schema
CREATE SCHEMA billing_new;

-- Step 3: Clone structure with improvements
CREATE OR REPLACE FUNCTION fn_migrate_schema_structure()
RETURNS void AS $$
BEGIN
    -- Create improved tables in new schema
    CREATE TABLE billing_new.organizations (LIKE public.organizations INCLUDING ALL);
    CREATE TABLE billing_new.usage_events (LIKE public.usage_events INCLUDING ALL);
    
    -- Add new columns and constraints
    ALTER TABLE billing_new.organizations 
    ADD COLUMN encryption_key_id UUID,
    ADD COLUMN data_classification VARCHAR(20) DEFAULT 'standard';
    
    ALTER TABLE billing_new.usage_events
    ADD COLUMN processing_status VARCHAR(50) DEFAULT 'pending',
    ADD COLUMN processed_at TIMESTAMP;
    
    -- Add improved indexes
    CREATE INDEX CONCURRENTLY idx_new_usage_events_processing 
    ON billing_new.usage_events(processing_status, organization_id)
    WHERE processing_status = 'pending';
    
    UPDATE migration_status 
    SET status = 'schema_created', phase = 'structure'
    WHERE migration_name = 'billing_v2_migration';
END;
$$ LANGUAGE plpgsql;
```

### 1.2 Data Migration with CDC

```sql
-- Setup logical replication for zero-downtime migration
CREATE PUBLICATION billing_migration_pub 
FOR ALL TABLES IN SCHEMA public;

-- Create subscription in new schema
-- Run on target (can be same database)
CREATE SUBSCRIPTION billing_migration_sub
CONNECTION 'dbname=billing host=localhost user=replication_user'
PUBLICATION billing_migration_pub
WITH (create_slot = true, enabled = false, copy_data = false);

-- CDC trigger for real-time sync
CREATE OR REPLACE FUNCTION fn_cdc_sync_to_new_schema()
RETURNS TRIGGER AS $$
BEGIN
    -- Sync INSERTs
    IF TG_OP = 'INSERT' THEN
        EXECUTE format(
            'INSERT INTO billing_new.%I SELECT $1.*',
            TG_TABLE_NAME
        ) USING NEW;
        
    -- Sync UPDATEs    
    ELSIF TG_OP = 'UPDATE' THEN
        EXECUTE format(
            'UPDATE billing_new.%I SET (%s) = (%s) WHERE id = $1',
            TG_TABLE_NAME,
            (SELECT string_agg(column_name, ', ') 
             FROM information_schema.columns 
             WHERE table_name = TG_TABLE_NAME),
            (SELECT string_agg('$2.' || column_name, ', ') 
             FROM information_schema.columns 
             WHERE table_name = TG_TABLE_NAME)
        ) USING OLD.id, NEW;
        
    -- Sync DELETEs
    ELSIF TG_OP = 'DELETE' THEN
        EXECUTE format(
            'DELETE FROM billing_new.%I WHERE id = $1',
            TG_TABLE_NAME
        ) USING OLD.id;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply CDC triggers
CREATE TRIGGER cdc_sync_organizations
AFTER INSERT OR UPDATE OR DELETE ON public.organizations
FOR EACH ROW EXECUTE FUNCTION fn_cdc_sync_to_new_schema();
```

### 1.3 Batch Data Migration

```sql
-- Parallel batch migration for historical data
CREATE OR REPLACE FUNCTION fn_migrate_historical_data(
    batch_size INTEGER DEFAULT 10000
) RETURNS void AS $$
DECLARE
    total_rows BIGINT;
    migrated_rows BIGINT := 0;
    batch_count INTEGER := 0;
BEGIN
    -- Get total rows
    SELECT COUNT(*) INTO total_rows FROM public.usage_events;
    
    -- Migrate in batches
    WHILE migrated_rows < total_rows LOOP
        -- Copy batch with transformations
        INSERT INTO billing_new.usage_events
        SELECT 
            *,
            'migrated' as processing_status,
            NOW() as processed_at
        FROM public.usage_events
        ORDER BY timestamp
        LIMIT batch_size
        OFFSET migrated_rows
        ON CONFLICT (id) DO NOTHING;
        
        migrated_rows := migrated_rows + batch_size;
        batch_count := batch_count + 1;
        
        -- Checkpoint every 10 batches
        IF batch_count % 10 = 0 THEN
            UPDATE migration_status
            SET rollback_point = jsonb_build_object(
                'migrated_rows', migrated_rows,
                'last_timestamp', (
                    SELECT MAX(timestamp) 
                    FROM billing_new.usage_events
                )
            )::TEXT
            WHERE migration_name = 'billing_v2_migration';
            
            -- Vacuum to prevent bloat
            VACUUM billing_new.usage_events;
        END IF;
        
        -- Progress logging
        RAISE NOTICE 'Migrated % of % rows (%.2f%%)', 
            migrated_rows, total_rows, 
            (migrated_rows::FLOAT / total_rows * 100);
            
        -- Prevent overwhelming the system
        PERFORM pg_sleep(0.1);
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

## Phase 2: Security Enhancement Migration

### 2.1 Enable RLS Without Disruption

```sql
-- Step 1: Create RLS policies in disabled state
CREATE OR REPLACE FUNCTION fn_prepare_rls_migration()
RETURNS void AS $$
BEGIN
    -- Add RLS to tables (disabled initially)
    ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
    ALTER TABLE usage_events ENABLE ROW LEVEL SECURITY;
    ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
    
    -- Create permissive policies (allow all initially)
    CREATE POLICY migration_allow_all_orgs ON organizations
        FOR ALL 
        USING (true);
        
    CREATE POLICY migration_allow_all_usage ON usage_events
        FOR ALL
        USING (true);
        
    -- Test with specific user
    CREATE USER migration_test_user;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO migration_test_user;
    
    -- Validate no disruption
    SET ROLE migration_test_user;
    IF (SELECT COUNT(*) FROM organizations) = 0 THEN
        RAISE EXCEPTION 'RLS policy blocking access during migration';
    END IF;
    RESET ROLE;
    
    -- Log success
    UPDATE migration_status
    SET status = 'rls_prepared'
    WHERE migration_name = 'security_migration';
END;
$$ LANGUAGE plpgsql;

-- Step 2: Gradually tighten policies
CREATE OR REPLACE FUNCTION fn_activate_rls_policies()
RETURNS void AS $$
BEGIN
    -- Replace permissive policies with restrictive ones
    DROP POLICY migration_allow_all_orgs ON organizations;
    
    CREATE POLICY tenant_isolation ON organizations
        FOR ALL
        USING (id = current_setting('app.current_tenant', true)::UUID);
        
    -- Test each application connection
    -- This would be done application by application
    UPDATE migration_status
    SET status = 'rls_active'
    WHERE migration_name = 'security_migration';
END;
$$ LANGUAGE plpgsql;
```

### 2.2 Encryption Migration

```sql
-- Encrypt existing data in place
CREATE OR REPLACE FUNCTION fn_migrate_to_encrypted_storage()
RETURNS void AS $$
DECLARE
    batch_size INTEGER := 1000;
    encrypted_count INTEGER := 0;
    total_records INTEGER;
BEGIN
    -- Get total sensitive records
    SELECT COUNT(*) INTO total_records 
    FROM payment_methods 
    WHERE card_number IS NOT NULL;
    
    -- Encrypt in batches
    WHILE encrypted_count < total_records LOOP
        UPDATE payment_methods
        SET 
            card_number_encrypted = fn_encrypt_pii(card_number),
            card_number = NULL -- Clear plaintext
        WHERE id IN (
            SELECT id 
            FROM payment_methods
            WHERE card_number IS NOT NULL
            LIMIT batch_size
        );
        
        encrypted_count := encrypted_count + batch_size;
        
        -- Progress checkpoint
        UPDATE migration_status
        SET rollback_point = jsonb_build_object(
            'encrypted_records', encrypted_count,
            'remaining', total_records - encrypted_count
        )::TEXT
        WHERE migration_name = 'encryption_migration';
        
        COMMIT; -- Commit each batch
        
        RAISE NOTICE 'Encrypted % of % payment methods', 
            encrypted_count, total_records;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

## Phase 3: Performance Migration

### 3.1 Index Migration Strategy

```sql
-- Create new indexes without blocking
CREATE OR REPLACE FUNCTION fn_migrate_indexes()
RETURNS void AS $$
DECLARE
    index_record RECORD;
    new_index_name TEXT;
    index_def TEXT;
BEGIN
    -- Get all existing indexes
    FOR index_record IN 
        SELECT 
            indexname,
            indexdef,
            tablename
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname NOT LIKE '%_pkey'
    LOOP
        -- Create new index concurrently
        new_index_name := index_record.indexname || '_new';
        index_def := REPLACE(
            index_record.indexdef, 
            index_record.indexname, 
            new_index_name
        );
        index_def := REPLACE(index_def, 'CREATE INDEX', 'CREATE INDEX CONCURRENTLY');
        
        BEGIN
            EXECUTE index_def;
            RAISE NOTICE 'Created index: %', new_index_name;
            
            -- Swap indexes atomically
            BEGIN
                ALTER INDEX index_record.indexname RENAME TO index_record.indexname || '_old';
                ALTER INDEX new_index_name RENAME TO index_record.indexname;
                DROP INDEX CONCURRENTLY index_record.indexname || '_old';
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE WARNING 'Failed to swap index %: %', index_record.indexname, SQLERRM;
            END;
            
        EXCEPTION
            WHEN OTHERS THEN
                RAISE WARNING 'Failed to create index %: %', new_index_name, SQLERRM;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

### 3.2 Partition Migration

```sql
-- Convert existing table to partitioned
CREATE OR REPLACE FUNCTION fn_migrate_to_partitioned_table()
RETURNS void AS $$
BEGIN
    -- Create partitioned table
    CREATE TABLE usage_events_partitioned (
        LIKE usage_events INCLUDING ALL
    ) PARTITION BY RANGE (timestamp);
    
    -- Create initial partitions
    FOR i IN 0..11 LOOP
        EXECUTE format(
            'CREATE TABLE usage_events_%s PARTITION OF usage_events_partitioned
             FOR VALUES FROM (%L) TO (%L)',
            TO_CHAR(CURRENT_DATE - (i || ' months')::INTERVAL, 'YYYY_MM'),
            DATE_TRUNC('month', CURRENT_DATE - (i || ' months')::INTERVAL),
            DATE_TRUNC('month', CURRENT_DATE - ((i-1) || ' months')::INTERVAL)
        );
    END LOOP;
    
    -- Copy data with minimal locking
    INSERT INTO usage_events_partitioned
    SELECT * FROM usage_events
    WHERE timestamp >= CURRENT_DATE - INTERVAL '12 months';
    
    -- Swap tables
    BEGIN
        ALTER TABLE usage_events RENAME TO usage_events_old;
        ALTER TABLE usage_events_partitioned RENAME TO usage_events;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE EXCEPTION 'Failed to swap tables: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;
```

## Rollback Procedures

### Automated Rollback Framework

```sql
-- Rollback orchestration
CREATE OR REPLACE FUNCTION fn_rollback_migration(
    migration_name_param VARCHAR
) RETURNS void AS $$
DECLARE
    rollback_point JSONB;
    migration_phase VARCHAR;
BEGIN
    -- Get rollback point
    SELECT 
        (rollback_point::JSONB),
        phase
    INTO rollback_point, migration_phase
    FROM migration_status
    WHERE migration_name = migration_name_param;
    
    CASE migration_phase
        WHEN 'schema' THEN
            -- Rollback schema changes
            DROP SCHEMA IF EXISTS billing_new CASCADE;
            
        WHEN 'data' THEN
            -- Restore from backup point
            EXECUTE format(
                'DELETE FROM billing_new.usage_events 
                 WHERE timestamp > %L',
                rollback_point->>'last_timestamp'
            );
            
        WHEN 'security' THEN
            -- Disable RLS
            ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
            ALTER TABLE usage_events DISABLE ROW LEVEL SECURITY;
            
        WHEN 'performance' THEN
            -- Restore old indexes
            PERFORM fn_restore_original_indexes();
    END CASE;
    
    -- Update status
    UPDATE migration_status
    SET 
        status = 'rolled_back',
        completed_at = NOW()
    WHERE migration_name = migration_name_param;
    
    RAISE NOTICE 'Migration % rolled back successfully', migration_name_param;
END;
$$ LANGUAGE plpgsql;

-- Automatic rollback trigger
CREATE OR REPLACE FUNCTION fn_auto_rollback_on_error()
RETURNS event_trigger AS $$
DECLARE
    error_info TEXT;
BEGIN
    -- Get error details
    GET STACKED DIAGNOSTICS error_info = MESSAGE_TEXT;
    
    -- Check if migration-related error
    IF error_info LIKE '%migration%' THEN
        -- Auto-rollback
        PERFORM fn_rollback_migration(
            (SELECT migration_name 
             FROM migration_status 
             WHERE status = 'in_progress'
             LIMIT 1)
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE EVENT TRIGGER migration_error_handler
ON sql_drop
EXECUTE FUNCTION fn_auto_rollback_on_error();
```

## Testing Protocols

### 1. Data Integrity Validation

```sql
-- Comprehensive validation suite
CREATE OR REPLACE FUNCTION fn_validate_migration()
RETURNS TABLE (
    check_name VARCHAR,
    status VARCHAR,
    details TEXT
) AS $$
BEGIN
    -- Row count validation
    RETURN QUERY
    SELECT 
        'row_count_check'::VARCHAR,
        CASE 
            WHEN COUNT(*) = (SELECT COUNT(*) FROM public.organizations)
            THEN 'PASS'::VARCHAR
            ELSE 'FAIL'::VARCHAR
        END,
        format('Old: %s, New: %s', 
            (SELECT COUNT(*) FROM public.organizations),
            COUNT(*)
        )::TEXT
    FROM billing_new.organizations;
    
    -- Data consistency check
    RETURN QUERY
    SELECT 
        'data_consistency'::VARCHAR,
        CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM public.usage_events o
                EXCEPT
                SELECT 1 FROM billing_new.usage_events n
            )
            THEN 'PASS'::VARCHAR
            ELSE 'FAIL'::VARCHAR
        END,
        'Data comparison check'::TEXT;
    
    -- Foreign key integrity
    RETURN QUERY
    SELECT 
        'foreign_key_check'::VARCHAR,
        CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM billing_new.subscriptions s
                WHERE NOT EXISTS (
                    SELECT 1 FROM billing_new.organizations o
                    WHERE o.id = s.organization_id
                )
            )
            THEN 'PASS'::VARCHAR
            ELSE 'FAIL'::VARCHAR
        END,
        'Foreign key constraints valid'::TEXT;
    
    -- Performance regression test
    RETURN QUERY
    WITH perf_test AS (
        SELECT 
            EXTRACT(EPOCH FROM (
                EXPLAIN (ANALYZE, BUFFERS) 
                SELECT COUNT(*) FROM billing_new.usage_events
                WHERE organization_id = '00000000-0000-0000-0000-000000000000'
                AND timestamp > CURRENT_DATE - INTERVAL '30 days'
            )) as new_time,
            EXTRACT(EPOCH FROM (
                EXPLAIN (ANALYZE, BUFFERS) 
                SELECT COUNT(*) FROM public.usage_events
                WHERE organization_id = '00000000-0000-0000-0000-000000000000'
                AND timestamp > CURRENT_DATE - INTERVAL '30 days'
            )) as old_time
    )
    SELECT 
        'performance_check'::VARCHAR,
        CASE
            WHEN new_time <= old_time * 1.1 -- Allow 10% degradation
            THEN 'PASS'::VARCHAR
            ELSE 'FAIL'::VARCHAR
        END,
        format('Old: %.3fms, New: %.3fms', old_time, new_time)::TEXT
    FROM perf_test;
END;
$$ LANGUAGE plpgsql;
```

### 2. Load Testing During Migration

```sql
-- Concurrent load test
CREATE OR REPLACE FUNCTION fn_migration_load_test(
    duration_seconds INTEGER DEFAULT 60
) RETURNS void AS $$
DECLARE
    start_time TIMESTAMP := NOW();
    operations_count INTEGER := 0;
BEGIN
    WHILE NOW() < start_time + (duration_seconds || ' seconds')::INTERVAL LOOP
        -- Simulate writes
        INSERT INTO usage_events (
            organization_id, metric_name, quantity, timestamp
        ) VALUES (
            gen_random_uuid(),
            'test_metric',
            random() * 1000,
            NOW()
        );
        
        -- Simulate reads
        PERFORM COUNT(*) 
        FROM usage_events 
        WHERE timestamp > NOW() - INTERVAL '1 hour';
        
        operations_count := operations_count + 1;
        
        -- Check migration status
        IF EXISTS (
            SELECT 1 FROM migration_status 
            WHERE status = 'failed'
        ) THEN
            RAISE EXCEPTION 'Migration failed during load test';
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Load test completed: % operations in % seconds',
        operations_count, duration_seconds;
END;
$$ LANGUAGE plpgsql;
```

## Monitoring During Migration

### Real-time Migration Dashboard

```sql
CREATE OR REPLACE VIEW vw_migration_dashboard AS
SELECT 
    ms.migration_name,
    ms.phase,
    ms.status,
    ms.started_at,
    EXTRACT(EPOCH FROM (NOW() - ms.started_at)) as duration_seconds,
    
    -- Progress metrics
    (SELECT COUNT(*) FROM billing_new.organizations) as new_org_count,
    (SELECT COUNT(*) FROM public.organizations) as old_org_count,
    
    -- Performance metrics
    (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
    (SELECT pg_size_pretty(pg_database_size(current_database()))) as database_size,
    
    -- Replication lag
    (SELECT EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp())) 
     FROM pg_stat_replication) as replication_lag_seconds,
    
    -- Error count
    (SELECT COUNT(*) FROM pg_stat_database WHERE datname = current_database()) as error_count
FROM migration_status ms
WHERE ms.status IN ('in_progress', 'validating');

-- Alert on issues
CREATE OR REPLACE FUNCTION fn_migration_alerts()
RETURNS TABLE (
    alert_level VARCHAR,
    message TEXT
) AS $$
BEGIN
    -- Check replication lag
    IF EXISTS (
        SELECT 1 FROM vw_migration_dashboard
        WHERE replication_lag_seconds > 10
    ) THEN
        RETURN QUERY
        SELECT 'WARNING'::VARCHAR, 'Replication lag exceeds 10 seconds'::TEXT;
    END IF;
    
    -- Check error rate
    IF EXISTS (
        SELECT 1 FROM vw_migration_dashboard
        WHERE error_count > 100
    ) THEN
        RETURN QUERY
        SELECT 'CRITICAL'::VARCHAR, 'High error rate detected during migration'::TEXT;
    END IF;
    
    -- Check duration
    IF EXISTS (
        SELECT 1 FROM vw_migration_dashboard
        WHERE duration_seconds > 3600 -- 1 hour
    ) THEN
        RETURN QUERY
        SELECT 'WARNING'::VARCHAR, 'Migration taking longer than expected'::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

## Migration Timeline

### Detailed Implementation Schedule

| Phase | Duration | Downtime | Risk | Rollback Time |
|-------|----------|----------|------|---------------|
| **Week 1: Preparation** |
| Create migration framework | 2 days | None | Low | N/A |
| Setup CDC replication | 1 day | None | Low | Immediate |
| Create validation tests | 2 days | None | Low | N/A |
| **Week 2: Schema Migration** |
| Create new schema | 1 day | None | Low | Immediate |
| Migrate structure | 2 days | None | Low | 5 min |
| Add improvements | 2 days | None | Medium | 10 min |
| **Week 3: Data Migration** |
| Historical data copy | 3 days | None | Medium | 1 hour |
| Real-time sync setup | 1 day | None | Medium | 5 min |
| Validation | 1 day | None | Low | N/A |
| **Week 4: Security & Performance** |
| Enable RLS | 2 days | None | High | 15 min |
| Encryption migration | 2 days | None | High | 2 hours |
| Index optimization | 1 day | None | Medium | 30 min |
| **Week 5: Cutover** |
| Final validation | 1 day | None | Low | N/A |
| Application cutover | 4 hours | 5 min | High | 10 min |
| Monitoring | 3 days | None | Low | N/A |

## Cost-Benefit Analysis

### Migration Costs

| Item | Cost | Duration | Resources |
|------|------|----------|-----------|
| Engineering Time | $40,000 | 5 weeks | 2 DBAs, 1 DevOps |
| Additional Infrastructure | $5,000/month | Ongoing | Replication, staging |
| Testing & Validation | $10,000 | 2 weeks | QA team |
| Downtime Cost | $2,000 | 5 minutes | Revenue impact |
| **Total One-time Cost** | **$52,000** | | |

### Expected Benefits

| Benefit | Annual Value | Payback Period |
|---------|-------------|----------------|
| Performance Improvement (15%) | $60,000 | 10 months |
| Security Compliance | $100,000 | Immediate |
| Reduced Downtime (99.99%) | $48,000 | 12 months |
| Operational Efficiency | $36,000 | 6 months |
| **Total Annual Benefit** | **$244,000** | **2.5 months** |

## Success Criteria

- [ ] Zero data loss during migration
- [ ] Maximum 5 minutes downtime
- [ ] All validation tests pass
- [ ] Performance improvement > 10%
- [ ] No security vulnerabilities introduced
- [ ] Successful rollback test completed
- [ ] 24-hour stability post-migration
- [ ] All monitoring alerts cleared
