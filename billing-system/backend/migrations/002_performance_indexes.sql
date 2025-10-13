-- Performance optimization indexes for ValueVerse Billing System
-- Target: Support 1M events/minute with <100ms p95 response time

-- ==================== Usage Events Indexes ====================
-- Primary query patterns: by organization, metric, and time range

-- Composite index for usage queries (most common query pattern)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usage_events_org_metric_time 
ON usage_events(organization_id, metric_name, timestamp DESC)
WHERE timestamp > NOW() - INTERVAL '90 days';

-- Partial index for recent data (hot data optimization)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usage_events_recent 
ON usage_events(timestamp DESC)
WHERE timestamp > NOW() - INTERVAL '7 days';

-- Index for idempotency checks
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_usage_events_idempotency 
ON usage_events(idempotency_key)
WHERE idempotency_key IS NOT NULL;

-- TimescaleDB specific optimizations
SELECT add_retention_policy('usage_events', INTERVAL '1 year');
SELECT add_compression_policy('usage_events', INTERVAL '7 days');

-- Create continuous aggregate for hourly rollups
CREATE MATERIALIZED VIEW IF NOT EXISTS usage_events_hourly
WITH (timescaledb.continuous) AS
SELECT 
    organization_id,
    metric_name,
    time_bucket('1 hour', timestamp) AS hour,
    SUM(quantity) as total_quantity,
    COUNT(*) as event_count,
    AVG(quantity) as avg_quantity,
    MAX(quantity) as max_quantity
FROM usage_events
GROUP BY organization_id, metric_name, hour
WITH NO DATA;

-- Add retention policy to continuous aggregate
SELECT add_continuous_aggregate_policy('usage_events_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- ==================== Subscriptions Indexes ====================

-- Index for active subscription lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_org_status 
ON subscriptions(organization_id, status)
WHERE status IN ('active', 'trialing');

-- Index for billing period queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_period 
ON subscriptions(current_period_start, current_period_end)
WHERE status = 'active';

-- Index for subscription lifecycle
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscriptions_dates 
ON subscriptions(created_at, updated_at, canceled_at);

-- ==================== Invoices Indexes ====================

-- Index for invoice queries by organization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_org_status 
ON invoices(organization_id, status, created_at DESC);

-- Index for due invoices
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_due 
ON invoices(due_date, status)
WHERE status IN ('open', 'past_due');

-- Index for invoice amount queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_amount 
ON invoices(total, currency)
WHERE status = 'paid';

-- ==================== Billing Transactions Indexes ====================

-- Index for transaction queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_org_status 
ON billing_transactions(organization_id, status, created_at DESC);

-- Index for payment provider queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_provider 
ON billing_transactions(provider_transaction_id, provider)
WHERE provider_transaction_id IS NOT NULL;

-- ==================== Pricing Rules Indexes ====================

-- Index for pricing lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pricing_rules_plan_metric 
ON pricing_rules(plan_id, metric_name, is_active)
WHERE is_active = true;

-- ==================== Usage Limits Indexes ====================

-- Index for limit checks
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_usage_limits_sub_metric 
ON usage_limits(subscription_id, metric_name)
WHERE action_on_exceed = 'block';

-- ==================== Payment Methods Indexes ====================

-- Index for default payment method
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payment_methods_org_default 
ON payment_methods(organization_id, is_default)
WHERE is_default = true;

-- ==================== Organizations Indexes ====================

-- Index for organization lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_organizations_slug 
ON organizations(slug)
WHERE status = 'active';

-- ==================== Query Statistics ====================

-- Create statistics for better query planning
ANALYZE organizations;
ANALYZE subscriptions;
ANALYZE subscription_plans;
ANALYZE usage_events;
ANALYZE invoices;
ANALYZE billing_transactions;
ANALYZE pricing_rules;
ANALYZE usage_limits;
ANALYZE payment_methods;

-- ==================== Partitioning Strategy ====================

-- Create partitions for usage_events by month (if not using TimescaleDB)
-- This is handled automatically by TimescaleDB, but shown for reference
/*
CREATE TABLE IF NOT EXISTS usage_events_2024_01 PARTITION OF usage_events
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS usage_events_2024_02 PARTITION OF usage_events
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
*/

-- ==================== Performance Views ====================

-- View for quick MRR calculation
CREATE OR REPLACE VIEW monthly_recurring_revenue AS
SELECT 
    sp.currency,
    SUM(sp.base_price) as mrr,
    COUNT(DISTINCT s.organization_id) as active_customers,
    AVG(sp.base_price) as arpu
FROM subscriptions s
JOIN subscription_plans sp ON s.plan_id = sp.id
WHERE s.status IN ('active', 'trialing')
GROUP BY sp.currency;

-- View for usage summary
CREATE OR REPLACE VIEW usage_summary_current_month AS
SELECT 
    organization_id,
    metric_name,
    SUM(quantity) as total_usage,
    COUNT(*) as event_count,
    DATE_TRUNC('month', CURRENT_DATE) as month
FROM usage_events
WHERE timestamp >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY organization_id, metric_name;

-- ==================== Connection Pooling Configuration ====================

-- Recommended PostgreSQL configuration for high throughput
-- Add to postgresql.conf:
/*
max_connections = 200
shared_buffers = 8GB
effective_cache_size = 24GB
maintenance_work_mem = 2GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 2GB
max_wal_size = 8GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
*/

-- ==================== Monitoring Queries ====================

-- Query to check index usage
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Query to find slow queries
CREATE OR REPLACE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time
FROM pg_stat_statements
WHERE mean_time > 100  -- Queries taking more than 100ms on average
ORDER BY mean_time DESC
LIMIT 20;
