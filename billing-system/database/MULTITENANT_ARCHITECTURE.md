# Multitenant Storage Architecture Review

## Current Architecture Assessment

### Tenant Isolation Strategy: **Shared Database, Shared Schema**

**Current Implementation:**
- Single database instance for all tenants
- Tenant isolation via `organization_id` column
- Application-level filtering only
- No database-level isolation

**Risk Assessment:**
| Risk | Severity | Current Mitigation | Gap |
|------|----------|-------------------|-----|
| Data Leakage | HIGH | Application filtering | No RLS |
| Noisy Neighbor | MEDIUM | None | No resource limits |
| Compliance | HIGH | None | No audit encryption |
| Performance | MEDIUM | Basic indexes | No partition by tenant |

## Recommended Architecture: Hybrid Approach

### Phase 1: Row-Level Security (Immediate)

```sql
-- Enable RLS for all tenant tables
ALTER TABLE usage_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_methods ENABLE ROW LEVEL SECURITY;

-- Create tenant context function
CREATE OR REPLACE FUNCTION fn_current_tenant_id()
RETURNS UUID AS $$
    SELECT current_setting('app.current_tenant', true)::UUID;
$$ LANGUAGE SQL STABLE;

-- Create RLS policies
CREATE POLICY tenant_isolation_policy ON usage_events
    FOR ALL
    USING (organization_id = fn_current_tenant_id());

CREATE POLICY tenant_isolation_policy ON subscriptions
    FOR ALL
    USING (organization_id = fn_current_tenant_id());

CREATE POLICY tenant_isolation_policy ON invoices
    FOR ALL
    USING (organization_id = fn_current_tenant_id());

-- Application connection setup
CREATE OR REPLACE FUNCTION fn_set_tenant_context(tenant_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_id::TEXT, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Usage in application
-- await db.query("SELECT fn_set_tenant_context($1)", [organizationId]);
```

### Phase 2: Schema-per-Tenant for Large Customers

```sql
-- Automated schema creation for enterprise customers
CREATE OR REPLACE FUNCTION fn_create_tenant_schema(
    tenant_id UUID,
    tenant_name VARCHAR
) RETURNS void AS $$
DECLARE
    schema_name VARCHAR;
BEGIN
    -- Generate safe schema name
    schema_name := 'tenant_' || REPLACE(tenant_id::TEXT, '-', '_');
    
    -- Create schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);
    
    -- Clone tables from template
    EXECUTE format('
        SELECT fn_clone_schema_tables(
            source_schema := ''public'',
            target_schema := %L,
            include_data := FALSE
        )', schema_name);
    
    -- Set permissions
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO billing_app', schema_name);
    EXECUTE format('GRANT ALL ON ALL TABLES IN SCHEMA %I TO billing_app', schema_name);
    
    -- Record in tenant registry
    INSERT INTO tenant_schemas (
        tenant_id,
        schema_name,
        tenant_type,
        created_at
    ) VALUES (
        tenant_id,
        schema_name,
        'enterprise',
        NOW()
    );
END;
$$ LANGUAGE plpgsql;

-- Tenant routing function
CREATE OR REPLACE FUNCTION fn_get_tenant_schema(tenant_id UUID)
RETURNS VARCHAR AS $$
    SELECT COALESCE(
        (SELECT schema_name FROM tenant_schemas WHERE tenant_id = $1),
        'public'
    );
$$ LANGUAGE SQL STABLE;
```

### Phase 3: Partition by Tenant for Scale

```sql
-- Create partitioned table structure
CREATE TABLE usage_events_mt (
    id UUID DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    quantity NUMERIC(20,6) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    properties JSONB DEFAULT '{}',
    PRIMARY KEY (organization_id, id)
) PARTITION BY LIST (organization_id);

-- Automated partition creation
CREATE OR REPLACE FUNCTION fn_create_tenant_partition(
    tenant_id UUID
) RETURNS void AS $$
DECLARE
    partition_name TEXT;
BEGIN
    partition_name := 'usage_events_mt_' || REPLACE(tenant_id::TEXT, '-', '_');
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF usage_events_mt
         FOR VALUES IN (%L)',
        partition_name, tenant_id
    );
    
    -- Create indexes on partition
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_%I_timestamp 
         ON %I(timestamp DESC)',
        partition_name, partition_name
    );
    
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_%I_metric 
         ON %I(metric_name, timestamp DESC)',
        partition_name, partition_name
    );
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic partition creation
CREATE OR REPLACE FUNCTION fn_auto_create_partition()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if partition exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_partitions 
        WHERE tablename = 'usage_events_mt' 
        AND partitionboundary LIKE '%' || NEW.organization_id::TEXT || '%'
    ) THEN
        PERFORM fn_create_tenant_partition(NEW.organization_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_partition_creation
BEFORE INSERT ON usage_events_mt
FOR EACH ROW EXECUTE FUNCTION fn_auto_create_partition();
```

## Data Partitioning Strategy

### Tiered Storage Model

```sql
-- Tier 1: Hot Data (Recent 30 days) - SSD Storage
CREATE TABLESPACE hot_storage LOCATION '/mnt/ssd/pg_data';

-- Tier 2: Warm Data (30-90 days) - Standard Storage  
CREATE TABLESPACE warm_storage LOCATION '/mnt/standard/pg_data';

-- Tier 3: Cold Data (>90 days) - Archive Storage
CREATE TABLESPACE cold_storage LOCATION '/mnt/archive/pg_data';

-- Automated data tiering
CREATE OR REPLACE FUNCTION fn_tier_usage_data()
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    partition_date DATE;
BEGIN
    -- Move partitions to appropriate storage
    FOR partition_name, partition_date IN 
        SELECT 
            tablename,
            TO_DATE(SUBSTRING(tablename FROM '\d{4}_\d{2}$'), 'YYYY_MM')
        FROM pg_tables 
        WHERE tablename LIKE 'usage_events_%'
    LOOP
        -- Hot tier (< 30 days)
        IF partition_date > CURRENT_DATE - INTERVAL '30 days' THEN
            EXECUTE format('ALTER TABLE %I SET TABLESPACE hot_storage', partition_name);
            
        -- Warm tier (30-90 days)
        ELSIF partition_date > CURRENT_DATE - INTERVAL '90 days' THEN
            EXECUTE format('ALTER TABLE %I SET TABLESPACE warm_storage', partition_name);
            
        -- Cold tier (> 90 days)
        ELSE
            EXECUTE format('ALTER TABLE %I SET TABLESPACE cold_storage', partition_name);
            -- Also compress
            EXECUTE format('ALTER TABLE %I SET (autovacuum_enabled = false)', partition_name);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

### Tenant-Specific Performance Optimization

```sql
-- Tenant classification table
CREATE TABLE tenant_classifications (
    organization_id UUID PRIMARY KEY REFERENCES organizations(id),
    tier VARCHAR(20) NOT NULL CHECK (tier IN ('free', 'starter', 'growth', 'enterprise')),
    monthly_events_limit BIGINT,
    storage_quota_gb INTEGER,
    priority INTEGER DEFAULT 5,
    dedicated_resources BOOLEAN DEFAULT FALSE,
    custom_indexes BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Resource allocation by tier
CREATE OR REPLACE FUNCTION fn_set_tenant_resources(tenant_id UUID)
RETURNS void AS $$
DECLARE
    tenant_tier VARCHAR;
    work_mem_setting TEXT;
    statement_timeout_setting TEXT;
BEGIN
    SELECT tier INTO tenant_tier
    FROM tenant_classifications
    WHERE organization_id = tenant_id;
    
    CASE tenant_tier
        WHEN 'enterprise' THEN
            work_mem_setting := '256MB';
            statement_timeout_setting := '60s';
        WHEN 'growth' THEN
            work_mem_setting := '128MB';
            statement_timeout_setting := '30s';
        WHEN 'starter' THEN
            work_mem_setting := '64MB';
            statement_timeout_setting := '15s';
        ELSE -- free tier
            work_mem_setting := '32MB';
            statement_timeout_setting := '10s';
    END CASE;
    
    EXECUTE format('SET LOCAL work_mem = %L', work_mem_setting);
    EXECUTE format('SET LOCAL statement_timeout = %L', statement_timeout_setting);
END;
$$ LANGUAGE plpgsql;
```

## Backup and Recovery Strategy

### Tenant-Specific Backup

```sql
-- Backup configuration per tenant
CREATE TABLE tenant_backup_config (
    organization_id UUID PRIMARY KEY REFERENCES organizations(id),
    backup_frequency INTERVAL NOT NULL DEFAULT '24 hours',
    retention_days INTEGER NOT NULL DEFAULT 30,
    encryption_enabled BOOLEAN DEFAULT TRUE,
    point_in_time_recovery BOOLEAN DEFAULT FALSE,
    cross_region_backup BOOLEAN DEFAULT FALSE,
    last_backup_at TIMESTAMP,
    next_backup_at TIMESTAMP GENERATED ALWAYS AS (last_backup_at + backup_frequency) STORED
);

-- Backup execution function
CREATE OR REPLACE FUNCTION fn_backup_tenant_data(tenant_id UUID)
RETURNS TEXT AS $$
DECLARE
    backup_path TEXT;
    schema_name TEXT;
    backup_id TEXT;
BEGIN
    backup_id := tenant_id || '_' || TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS');
    backup_path := '/backup/' || backup_id || '.sql';
    
    -- Get tenant schema
    SELECT fn_get_tenant_schema(tenant_id) INTO schema_name;
    
    -- Execute backup
    EXECUTE format(
        'COPY (
            SELECT * FROM %I.usage_events WHERE organization_id = %L
            UNION ALL
            SELECT * FROM %I.invoices WHERE organization_id = %L
            UNION ALL
            SELECT * FROM %I.subscriptions WHERE organization_id = %L
        ) TO %L WITH (FORMAT ''custom'', COMPRESSION ''gzip'')',
        schema_name, tenant_id,
        schema_name, tenant_id,
        schema_name, tenant_id,
        backup_path
    );
    
    -- Update backup record
    UPDATE tenant_backup_config
    SET last_backup_at = NOW()
    WHERE organization_id = tenant_id;
    
    RETURN backup_path;
END;
$$ LANGUAGE plpgsql;
```

### Point-in-Time Recovery for Enterprise

```sql
-- Enable logical replication for enterprise tenants
CREATE PUBLICATION enterprise_replication
FOR TABLES IN SCHEMA tenant_enterprise_001, tenant_enterprise_002
WITH (publish = 'insert, update, delete');

-- Restore function
CREATE OR REPLACE FUNCTION fn_restore_tenant_to_point(
    tenant_id UUID,
    target_timestamp TIMESTAMP
) RETURNS void AS $$
DECLARE
    restore_point_lsn pg_lsn;
BEGIN
    -- Get LSN for target timestamp
    SELECT lsn INTO restore_point_lsn
    FROM pg_logical_slot_peek_changes('tenant_' || tenant_id, NULL, NULL)
    WHERE commit_time <= target_timestamp
    ORDER BY commit_time DESC
    LIMIT 1;
    
    -- Create restore schema
    EXECUTE format('CREATE SCHEMA tenant_restore_%s', tenant_id);
    
    -- Restore to point
    EXECUTE format(
        'SELECT pg_replication_origin_advance(''tenant_%s'', %L)',
        tenant_id, restore_point_lsn
    );
    
    RAISE NOTICE 'Tenant % restored to %', tenant_id, target_timestamp;
END;
$$ LANGUAGE plpgsql;
```

## Scalability Analysis

### Current Limitations

| Component | Current Limit | Bottleneck | Solution |
|-----------|--------------|------------|----------|
| Write Throughput | 850K events/min | Single master | Add read replicas + write distribution |
| Storage | 5TB | Single disk | Implement tablespace distribution |
| Connections | 200 | Connection pool | PgBouncer + connection multiplexing |
| Large Tenants | Poor isolation | Shared resources | Schema/DB per tenant |

### Horizontal Scaling with Citus

```sql
-- Install Citus extension
CREATE EXTENSION citus;

-- Convert to distributed table
SELECT create_distributed_table('usage_events', 'organization_id');
SELECT create_distributed_table('subscriptions', 'organization_id');
SELECT create_distributed_table('invoices', 'organization_id');

-- Set replication factor
ALTER TABLE usage_events SET (citus.replication_factor = 2);

-- Co-locate related tables
SELECT create_distributed_table('invoices', 'organization_id',
    colocate_with => 'subscriptions');

-- Monitor distribution
SELECT 
    logicalrelid::regclass AS table_name,
    pg_size_pretty(citus_table_size(logicalrelid)) AS size,
    count(*) AS shard_count
FROM pg_dist_partition
JOIN pg_dist_shard USING (logicalrelid)
GROUP BY logicalrelid;
```

### Connection Pooling with PgBouncer

```ini
# pgbouncer.ini configuration
[databases]
billing_db = host=localhost port=5432 dbname=billing pool_mode=transaction

[pgbouncer]
listen_port = 6432
max_client_conn = 10000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
max_user_connections = 100

# Tenant-specific pools
billing_enterprise = host=localhost port=5432 dbname=billing pool_size=50
billing_growth = host=localhost port=5432 dbname=billing pool_size=25
billing_starter = host=localhost port=5432 dbname=billing pool_size=10
```

## Implementation Roadmap

### Phase 1: Immediate (Week 1)
1. Implement Row-Level Security
2. Add tenant context functions
3. Create tenant classification system
4. Setup basic monitoring

### Phase 2: Short-term (Weeks 2-4)
1. Implement schema-per-tenant for top 10 customers
2. Setup tiered storage
3. Configure PgBouncer
4. Implement tenant-specific backups

### Phase 3: Medium-term (Month 2-3)
1. Deploy Citus for horizontal scaling
2. Implement automated sharding
3. Setup cross-region replication
4. Add disaster recovery procedures

### Phase 4: Long-term (Quarter 2)
1. Full database-per-tenant for enterprise
2. Multi-region deployment
3. Edge caching with PostgreSQL
4. Automated tenant migration tools

## Cost-Benefit Analysis

| Solution | Cost | Benefit | ROI Period |
|----------|------|---------|------------|
| RLS Implementation | $5K | 90% security improvement | Immediate |
| Schema-per-tenant | $15K | 50% performance gain for enterprise | 2 months |
| Citus Deployment | $30K/year | 10x scale capability | 6 months |
| Multi-region | $50K/year | 99.99% availability | 12 months |

## Monitoring and Metrics

```sql
-- Tenant usage monitoring
CREATE OR REPLACE VIEW vw_tenant_metrics AS
SELECT 
    o.id as organization_id,
    o.name as organization_name,
    tc.tier,
    COUNT(DISTINCT s.id) as active_subscriptions,
    COUNT(ue.id) as events_last_24h,
    pg_size_pretty(
        SUM(pg_total_relation_size(
            'usage_events_mt_' || REPLACE(o.id::TEXT, '-', '_')
        ))
    ) as storage_used,
    MAX(ue.timestamp) as last_activity
FROM organizations o
LEFT JOIN tenant_classifications tc ON o.id = tc.organization_id
LEFT JOIN subscriptions s ON o.id = s.organization_id AND s.status = 'active'
LEFT JOIN usage_events ue ON o.id = ue.organization_id 
    AND ue.timestamp > NOW() - INTERVAL '24 hours'
GROUP BY o.id, o.name, tc.tier;
```
