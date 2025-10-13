-- =====================================================
-- Critical Indexes Implementation
-- Execution Time: ~2 days
-- Priority: HIGH (Performance)
-- Target: Support 1M+ events/minute
-- =====================================================

-- STEP 1: Analyze current index usage
-- =====================================================

-- Drop unused indexes to reduce overhead
DO $$
DECLARE
    unused_index RECORD;
BEGIN
    FOR unused_index IN 
        SELECT 
            schemaname,
            tablename,
            indexname
        FROM pg_stat_user_indexes
        WHERE idx_scan = 0
        AND indexrelname NOT LIKE '%_pkey'
        AND schemaname = 'public'
        AND pg_relation_size(indexrelid) > 1000000 -- Only large indexes
    LOOP
        RAISE NOTICE 'Dropping unused index: %.%', unused_index.schemaname, unused_index.indexname;
        EXECUTE format('DROP INDEX IF EXISTS %I.%I', unused_index.schemaname, unused_index.indexname);
    END LOOP;
END;
$$;

-- STEP 2: Critical indexes for usage_events table
-- =====================================================

-- Primary query pattern: by org, metric, and time
DROP INDEX IF EXISTS idx_usage_events_org_metric_time;
CREATE INDEX CONCURRENTLY idx_usage_events_org_metric_time 
ON usage_events(organization_id, metric_name, timestamp DESC)
INCLUDE (quantity, unit)
WHERE timestamp > CURRENT_DATE - INTERVAL '90 days';

-- Hot data optimization (most recent data)
DROP INDEX IF EXISTS idx_usage_events_recent;
CREATE INDEX CONCURRENTLY idx_usage_events_recent 
ON usage_events(timestamp DESC)
INCLUDE (organization_id, metric_name, quantity)
WHERE timestamp > CURRENT_DATE - INTERVAL '7 days';

-- Idempotency check optimization
DROP INDEX IF EXISTS idx_usage_events_idempotency;
CREATE UNIQUE INDEX CONCURRENTLY idx_usage_events_idempotency 
ON usage_events(idempotency_key)
WHERE idempotency_key IS NOT NULL;

-- BRIN index for time-series data (space-efficient for large tables)
DROP INDEX IF EXISTS idx_usage_events_timestamp_brin;
CREATE INDEX idx_usage_events_timestamp_brin 
ON usage_events USING BRIN (timestamp)
WITH (pages_per_range = 128);

-- Hash index for exact organization lookups
DROP INDEX IF EXISTS idx_usage_events_org_hash;
CREATE INDEX CONCURRENTLY idx_usage_events_org_hash 
ON usage_events USING HASH (organization_id);

-- GIN index for JSONB properties searches
DROP INDEX IF EXISTS idx_usage_events_properties_gin;
CREATE INDEX CONCURRENTLY idx_usage_events_properties_gin 
ON usage_events USING GIN (properties)
WHERE properties IS NOT NULL;

-- STEP 3: Critical indexes for subscriptions table
-- =====================================================

-- Active subscriptions by organization
DROP INDEX IF EXISTS idx_subscriptions_org_active;
CREATE INDEX CONCURRENTLY idx_subscriptions_org_active 
ON subscriptions(organization_id, status)
INCLUDE (plan_id, current_period_end)
WHERE status IN ('active', 'trialing');

-- Subscriptions ending soon (for renewal processing)
DROP INDEX IF EXISTS idx_subscriptions_renewal;
CREATE INDEX CONCURRENTLY idx_subscriptions_renewal 
ON subscriptions(current_period_end, status)
INCLUDE (organization_id, plan_id)
WHERE status = 'active' 
AND current_period_end BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days';

-- Canceled subscriptions (for churn analysis)
DROP INDEX IF EXISTS idx_subscriptions_canceled;
CREATE INDEX CONCURRENTLY idx_subscriptions_canceled 
ON subscriptions(canceled_at DESC)
INCLUDE (organization_id, plan_id, cancel_reason)
WHERE canceled_at IS NOT NULL;

-- STEP 4: Critical indexes for invoices table
-- =====================================================

-- Open invoices by organization
DROP INDEX IF EXISTS idx_invoices_org_open;
CREATE INDEX CONCURRENTLY idx_invoices_org_open 
ON invoices(organization_id, status, created_at DESC)
INCLUDE (total, amount_due, due_date)
WHERE status IN ('open', 'draft');

-- Past due invoices (for dunning)
DROP INDEX IF EXISTS idx_invoices_past_due;
CREATE INDEX CONCURRENTLY idx_invoices_past_due 
ON invoices(due_date, status)
INCLUDE (organization_id, total, amount_due)
WHERE status = 'past_due' OR (status = 'open' AND due_date < CURRENT_DATE);

-- Invoices by billing period
DROP INDEX IF EXISTS idx_invoices_period;
CREATE INDEX CONCURRENTLY idx_invoices_period 
ON invoices(billing_period_start, billing_period_end)
INCLUDE (organization_id, subscription_id, total);

-- Invoice number lookup (unique)
DROP INDEX IF EXISTS idx_invoices_number_unique;
CREATE UNIQUE INDEX CONCURRENTLY idx_invoices_number_unique 
ON invoices(invoice_number);

-- STEP 5: Critical indexes for billing_transactions
-- =====================================================

-- Transactions by organization and status
DROP INDEX IF EXISTS idx_billing_transactions_org_status;
CREATE INDEX CONCURRENTLY idx_billing_transactions_org_status 
ON billing_transactions(organization_id, status, created_at DESC)
INCLUDE (amount, provider)
WHERE status IN ('pending', 'processing', 'succeeded');

-- Failed transactions (for retry logic)
DROP INDEX IF EXISTS idx_billing_transactions_failed;
CREATE INDEX CONCURRENTLY idx_billing_transactions_failed 
ON billing_transactions(created_at DESC, retry_count)
INCLUDE (organization_id, invoice_id, amount)
WHERE status = 'failed' AND retry_count < 3;

-- Provider transaction lookup
DROP INDEX IF EXISTS idx_billing_transactions_provider;
CREATE INDEX CONCURRENTLY idx_billing_transactions_provider 
ON billing_transactions(provider_transaction_id, provider)
WHERE provider_transaction_id IS NOT NULL;

-- STEP 6: Critical indexes for payment_methods
-- =====================================================

-- Default payment method per organization
DROP INDEX IF EXISTS idx_payment_methods_org_default;
CREATE UNIQUE INDEX CONCURRENTLY idx_payment_methods_org_default 
ON payment_methods(organization_id)
WHERE is_default = true;

-- Active payment methods
DROP INDEX IF EXISTS idx_payment_methods_active;
CREATE INDEX CONCURRENTLY idx_payment_methods_active 
ON payment_methods(organization_id, status)
INCLUDE (type, provider, exp_month, exp_year)
WHERE status = 'active';

-- STEP 7: Critical indexes for organizations
-- =====================================================

-- Organization slug lookup (unique)
DROP INDEX IF EXISTS idx_organizations_slug_unique;
CREATE UNIQUE INDEX CONCURRENTLY idx_organizations_slug_unique 
ON organizations(slug)
WHERE status = 'active';

-- Organizations by status
DROP INDEX IF EXISTS idx_organizations_status;
CREATE INDEX CONCURRENTLY idx_organizations_status 
ON organizations(status, created_at DESC)
INCLUDE (name, slug);

-- STEP 8: Critical indexes for pricing_rules
-- =====================================================

-- Active pricing rules by plan and metric
DROP INDEX IF EXISTS idx_pricing_rules_active;
CREATE INDEX CONCURRENTLY idx_pricing_rules_active 
ON pricing_rules(plan_id, metric_name, is_active)
INCLUDE (pricing_type, rules)
WHERE is_active = true;

-- STEP 9: Critical indexes for usage_limits
-- =====================================================

-- Active limits by subscription and metric
DROP INDEX IF EXISTS idx_usage_limits_active;
CREATE INDEX CONCURRENTLY idx_usage_limits_active 
ON usage_limits(subscription_id, metric_name)
INCLUDE (limit_value, current_usage, action_on_exceed)
WHERE reset_at > CURRENT_TIMESTAMP;

-- STEP 10: Covering indexes for common queries
-- =====================================================

-- Covering index for usage summary query
DROP INDEX IF EXISTS idx_usage_summary_covering;
CREATE INDEX CONCURRENTLY idx_usage_summary_covering 
ON usage_events(organization_id, timestamp DESC)
INCLUDE (metric_name, quantity)
WHERE timestamp > CURRENT_DATE - INTERVAL '30 days';

-- Covering index for billing overview query
DROP INDEX IF EXISTS idx_billing_overview_covering;
CREATE INDEX CONCURRENTLY idx_billing_overview_covering 
ON invoices(organization_id, created_at DESC)
INCLUDE (status, total, amount_due, due_date)
WHERE created_at > CURRENT_DATE - INTERVAL '12 months';

-- STEP 11: Partial indexes for specific conditions
-- =====================================================

-- High-value transactions
DROP INDEX IF EXISTS idx_high_value_transactions;
CREATE INDEX CONCURRENTLY idx_high_value_transactions 
ON billing_transactions(created_at DESC)
INCLUDE (organization_id, amount, status)
WHERE amount > 1000;

-- Trial subscriptions
DROP INDEX IF EXISTS idx_trial_subscriptions;
CREATE INDEX CONCURRENTLY idx_trial_subscriptions 
ON subscriptions(trial_end, organization_id)
WHERE status = 'trialing' AND trial_end IS NOT NULL;

-- STEP 12: Expression indexes for computed values
-- =====================================================

-- Index on date part of timestamp for daily aggregations
DROP INDEX IF EXISTS idx_usage_events_date;
CREATE INDEX CONCURRENTLY idx_usage_events_date 
ON usage_events(DATE(timestamp), organization_id, metric_name);

-- Index on month for monthly billing
DROP INDEX IF EXISTS idx_invoices_month;
CREATE INDEX CONCURRENTLY idx_invoices_month 
ON invoices(DATE_TRUNC('month', created_at), organization_id);

-- STEP 13: Create index statistics and analyze
-- =====================================================

-- Update table statistics for query planner
ANALYZE usage_events;
ANALYZE subscriptions;
ANALYZE invoices;
ANALYZE billing_transactions;
ANALYZE payment_methods;
ANALYZE organizations;
ANALYZE pricing_rules;
ANALYZE usage_limits;

-- STEP 14: Create index monitoring functions
-- =====================================================

-- Function to monitor index effectiveness
CREATE OR REPLACE FUNCTION analyze_index_effectiveness()
RETURNS TABLE (
    index_name TEXT,
    table_name TEXT,
    index_size TEXT,
    index_scans BIGINT,
    tuples_read BIGINT,
    tuples_fetched BIGINT,
    effectiveness_score NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.indexrelname::TEXT,
        i.tablename::TEXT,
        pg_size_pretty(pg_relation_size(i.indexrelid)),
        i.idx_scan,
        i.idx_tup_read,
        i.idx_tup_fetch,
        CASE 
            WHEN i.idx_scan > 0 THEN 
                ROUND((i.idx_tup_fetch::NUMERIC / NULLIF(i.idx_scan, 0)) * 100, 2)
            ELSE 0
        END
    FROM pg_stat_user_indexes i
    WHERE i.schemaname = 'public'
    ORDER BY i.idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to find missing indexes
CREATE OR REPLACE FUNCTION suggest_missing_indexes()
RETURNS TABLE (
    table_name TEXT,
    column_name TEXT,
    sequential_scans BIGINT,
    table_size TEXT,
    suggestion TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH table_scans AS (
        SELECT 
            schemaname,
            tablename,
            seq_scan,
            seq_tup_read,
            idx_scan,
            pg_relation_size(schemaname||'.'||tablename) as size
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
    )
    SELECT 
        ts.tablename::TEXT,
        a.attname::TEXT,
        ts.seq_scan,
        pg_size_pretty(ts.size),
        format('CREATE INDEX idx_%s_%s ON %s(%s)',
            ts.tablename, a.attname, ts.tablename, a.attname)::TEXT
    FROM table_scans ts
    CROSS JOIN LATERAL (
        SELECT attname
        FROM pg_attribute
        WHERE attrelid = (ts.schemaname||'.'||ts.tablename)::regclass
        AND attnum > 0
        AND NOT attisdropped
        AND attname IN ('organization_id', 'created_at', 'status', 'timestamp')
    ) a
    WHERE ts.seq_scan > 1000
    AND ts.seq_scan > ts.idx_scan
    ORDER BY ts.seq_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- STEP 15: Create index maintenance procedures
-- =====================================================

-- Automated index maintenance
CREATE OR REPLACE FUNCTION maintain_indexes()
RETURNS void AS $$
DECLARE
    index_record RECORD;
    bloat_threshold NUMERIC := 30; -- 30% bloat threshold
BEGIN
    -- Identify and rebuild bloated indexes
    FOR index_record IN 
        SELECT 
            schemaname,
            tablename,
            indexname,
            pg_relation_size(indexrelid) as index_size,
            ROUND(
                CASE WHEN pg_relation_size(indexrelid) > 0
                THEN (pg_relation_size(indexrelid) - pg_relation_size(indexrelid::regclass)) * 100.0 / 
                     pg_relation_size(indexrelid)
                ELSE 0 END, 2
            ) as bloat_percent
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        AND pg_relation_size(indexrelid) > 10485760 -- > 10MB
    LOOP
        IF index_record.bloat_percent > bloat_threshold THEN
            RAISE NOTICE 'Rebuilding bloated index: % (% bloat)', 
                index_record.indexname, index_record.bloat_percent;
            
            EXECUTE format('REINDEX INDEX CONCURRENTLY %I.%I',
                index_record.schemaname, index_record.indexname);
        END IF;
    END LOOP;
    
    -- Update statistics
    EXECUTE 'ANALYZE';
END;
$$ LANGUAGE plpgsql;

-- Schedule regular maintenance
-- Note: Requires pg_cron extension
-- SELECT cron.schedule('index-maintenance', '0 2 * * 0', 'SELECT maintain_indexes()');

-- STEP 16: Validation and monitoring
-- =====================================================

-- Create monitoring view for index usage
CREATE OR REPLACE VIEW vw_index_usage_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as size,
    CASE 
        WHEN idx_scan = 0 THEN 'UNUSED'
        WHEN idx_scan < 100 THEN 'RARELY_USED'
        WHEN idx_scan < 1000 THEN 'OCCASIONALLY_USED'
        ELSE 'FREQUENTLY_USED'
    END as usage_category,
    ROUND(
        CASE WHEN idx_scan > 0 
        THEN (idx_tup_fetch::NUMERIC / idx_scan)
        ELSE 0 END, 2
    ) as avg_tuples_per_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Validate critical indexes exist
DO $$
DECLARE
    missing_count INTEGER := 0;
    index_name TEXT;
BEGIN
    -- Check for critical indexes
    FOR index_name IN 
        SELECT unnest(ARRAY[
            'idx_usage_events_org_metric_time',
            'idx_usage_events_idempotency',
            'idx_subscriptions_org_active',
            'idx_invoices_org_open',
            'idx_billing_transactions_org_status'
        ])
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname = index_name
        ) THEN
            RAISE WARNING 'Missing critical index: %', index_name;
            missing_count := missing_count + 1;
        END IF;
    END LOOP;
    
    IF missing_count = 0 THEN
        RAISE NOTICE '==============================================';
        RAISE NOTICE 'Critical Indexes Implementation Complete';
        RAISE NOTICE '==============================================';
        RAISE NOTICE 'All critical indexes created successfully';
        RAISE NOTICE 'Run SELECT * FROM analyze_index_effectiveness() to monitor';
        RAISE NOTICE 'Run SELECT * FROM suggest_missing_indexes() for suggestions';
    ELSE
        RAISE EXCEPTION '% critical indexes are missing', missing_count;
    END IF;
END;
$$;
