#!/bin/bash

# =====================================================
# Database Security & Performance Implementation Script
# Executes all 4 critical migrations with safety checks
# =====================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-billing_db}"
DB_USER="${DB_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
LOG_FILE="migration_$(date +%Y%m%d_%H%M%S).log"

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p logs

# Logging function
log() {
    echo -e "${1}${2}${NC}" | tee -a "logs/$LOG_FILE"
}

# Error handler
error_exit() {
    log "$RED" "ERROR: $1"
    log "$YELLOW" "Rolling back changes..."
    rollback_all
    exit 1
}

# Success message
success() {
    log "$GREEN" "✓ $1"
}

# Warning message
warning() {
    log "$YELLOW" "⚠ $1"
}

# Info message
info() {
    log "$BLUE" "ℹ $1"
}

# Function to execute SQL and check result
execute_sql() {
    local sql_file=$1
    local description=$2
    
    info "Executing: $description"
    
    if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file" >> "logs/$LOG_FILE" 2>&1; then
        success "$description completed successfully"
        return 0
    else
        error_exit "$description failed"
        return 1
    fi
}

# Function to run SQL command
run_sql() {
    local sql_command=$1
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$sql_command" 2>/dev/null
}

# Backup database
backup_database() {
    info "Creating database backup..."
    local backup_file="$BACKUP_DIR/billing_db_$(date +%Y%m%d_%H%M%S).sql"
    
    if PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" > "$backup_file" 2>> "logs/$LOG_FILE"; then
        success "Backup created: $backup_file"
        echo "$backup_file" > "$BACKUP_DIR/latest_backup.txt"
    else
        error_exit "Failed to create database backup"
    fi
}

# Restore database from backup
restore_database() {
    if [ -f "$BACKUP_DIR/latest_backup.txt" ]; then
        local backup_file=$(cat "$BACKUP_DIR/latest_backup.txt")
        warning "Restoring database from: $backup_file"
        
        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$backup_file" 2>> "logs/$LOG_FILE"
        success "Database restored"
    else
        warning "No backup file found to restore"
    fi
}

# Rollback all changes
rollback_all() {
    warning "Starting rollback procedure..."
    
    # Rollback in reverse order
    rollback_audit_triggers
    rollback_indexes
    rollback_encryption
    rollback_rls
    
    info "Rollback completed"
}

# Individual rollback functions
rollback_rls() {
    info "Rolling back RLS..."
    run_sql "
        ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
        ALTER TABLE subscriptions DISABLE ROW LEVEL SECURITY;
        ALTER TABLE usage_events DISABLE ROW LEVEL SECURITY;
        ALTER TABLE invoices DISABLE ROW LEVEL SECURITY;
        ALTER TABLE payment_methods DISABLE ROW LEVEL SECURITY;
        ALTER TABLE billing_transactions DISABLE ROW LEVEL SECURITY;
    "
}

rollback_encryption() {
    info "Rolling back encryption..."
    run_sql "
        DROP TABLE IF EXISTS encryption_keys CASCADE;
        DROP TABLE IF EXISTS encryption_key_usage CASCADE;
        DROP FUNCTION IF EXISTS encrypt_sensitive_data(TEXT, UUID) CASCADE;
        DROP FUNCTION IF EXISTS decrypt_sensitive_data(BYTEA, UUID) CASCADE;
    "
}

rollback_indexes() {
    info "Rolling back indexes..."
    run_sql "
        DROP INDEX IF EXISTS idx_usage_events_org_metric_time;
        DROP INDEX IF EXISTS idx_usage_events_recent;
        DROP INDEX IF EXISTS idx_usage_events_idempotency;
    "
}

rollback_audit_triggers() {
    info "Rolling back audit triggers..."
    run_sql "
        DROP TRIGGER IF EXISTS audit_organizations ON organizations;
        DROP TRIGGER IF EXISTS audit_subscriptions ON subscriptions;
        DROP TRIGGER IF EXISTS audit_invoices ON invoices;
        DROP TABLE IF EXISTS audit_trail CASCADE;
        DROP FUNCTION IF EXISTS audit_trigger_function() CASCADE;
    "
}

# Test database connection
test_connection() {
    info "Testing database connection..."
    
    if run_sql "SELECT 1" > /dev/null 2>&1; then
        success "Database connection successful"
    else
        error_exit "Cannot connect to database"
    fi
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check if migration files exist
    for file in migrations/*.sql; do
        if [ ! -f "$file" ]; then
            error_exit "Migration file not found: $file"
        fi
    done
    
    # Check if required extensions are available
    if ! run_sql "SELECT 1 FROM pg_available_extensions WHERE name = 'pgcrypto'" | grep -q "1"; then
        error_exit "Required extension 'pgcrypto' not available"
    fi
    
    success "All prerequisites met"
}

# Validate RLS implementation
validate_rls() {
    info "Validating RLS implementation..."
    
    local rls_status=$(run_sql "SELECT COUNT(*) FROM check_rls_status() WHERE rls_enabled = true")
    if [ "$rls_status" -gt 0 ]; then
        success "RLS enabled on $rls_status tables"
    else
        warning "RLS validation failed"
        return 1
    fi
}

# Validate encryption
validate_encryption() {
    info "Validating encryption..."
    
    local enc_test=$(run_sql "SELECT decrypt_sensitive_data(encrypt_sensitive_data('test', NULL), NULL)")
    if echo "$enc_test" | grep -q "test"; then
        success "Encryption/decryption working"
    else
        warning "Encryption validation failed"
        return 1
    fi
}

# Validate indexes
validate_indexes() {
    info "Validating indexes..."
    
    local index_count=$(run_sql "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%'")
    if [ "$index_count" -gt 10 ]; then
        success "$index_count indexes created"
    else
        warning "Expected more indexes, found only $index_count"
        return 1
    fi
}

# Validate audit trail
validate_audit() {
    info "Validating audit trail..."
    
    # Perform a test operation
    run_sql "UPDATE organizations SET updated_at = NOW() WHERE id = (SELECT id FROM organizations LIMIT 1)"
    
    local audit_count=$(run_sql "SELECT COUNT(*) FROM audit_trail WHERE table_name = 'organizations'")
    if [ "$audit_count" -gt 0 ]; then
        success "Audit trail capturing events"
    else
        warning "Audit trail validation failed"
        return 1
    fi
}

# Main execution
main() {
    echo ""
    log "$BLUE" "================================================"
    log "$BLUE" "Database Security & Performance Implementation"
    log "$BLUE" "================================================"
    echo ""
    
    # Prompt for database password if not set
    if [ -z "$DB_PASS" ]; then
        echo -n "Enter database password for $DB_USER: "
        read -s DB_PASS
        echo ""
        export DB_PASS
    fi
    
    # Test connection
    test_connection
    
    # Check prerequisites
    check_prerequisites
    
    # Confirm execution
    warning "This will modify the database schema. Continue? (yes/no)"
    read -r response
    if [ "$response" != "yes" ]; then
        info "Aborted by user"
        exit 0
    fi
    
    # Create backup
    backup_database
    
    # Execute migrations
    info "Starting migrations..."
    echo ""
    
    # 1. Row-Level Security
    log "$GREEN" "=== Phase 1: Row-Level Security ==="
    execute_sql "migrations/003_row_level_security.sql" "Row-Level Security"
    validate_rls || warning "RLS validation had issues"
    echo ""
    
    # 2. Encryption at Rest
    log "$GREEN" "=== Phase 2: Encryption at Rest ==="
    execute_sql "migrations/004_encryption_at_rest.sql" "Encryption at Rest"
    validate_encryption || warning "Encryption validation had issues"
    echo ""
    
    # 3. Critical Indexes
    log "$GREEN" "=== Phase 3: Critical Indexes ==="
    execute_sql "migrations/005_critical_indexes.sql" "Critical Indexes"
    validate_indexes || warning "Index validation had issues"
    echo ""
    
    # 4. Audit Triggers
    log "$GREEN" "=== Phase 4: Audit Triggers ==="
    execute_sql "migrations/006_audit_triggers.sql" "Audit Triggers"
    validate_audit || warning "Audit validation had issues"
    echo ""
    
    # Final validation
    log "$GREEN" "=== Final Validation ==="
    
    # Check overall health
    info "Checking database health..."
    run_sql "SELECT * FROM verify_audit_trail_integrity()" | head -5
    
    # Performance check
    info "Running performance check..."
    run_sql "EXPLAIN ANALYZE SELECT COUNT(*) FROM usage_events WHERE organization_id = '00000000-0000-0000-0000-000000000000'" | grep "Execution Time"
    
    echo ""
    log "$GREEN" "================================================"
    log "$GREEN" "✅ All migrations completed successfully!"
    log "$GREEN" "================================================"
    echo ""
    
    info "Next steps:"
    echo "  1. Update application to use SecureDatabase class"
    echo "  2. Monitor security_audit_log for violations"
    echo "  3. Check vw_encryption_status for coverage"
    echo "  4. Review analyze_index_effectiveness() results"
    echo "  5. Verify audit_trail integrity daily"
    echo ""
    info "Logs saved to: logs/$LOG_FILE"
    info "Backup saved to: $(cat $BACKUP_DIR/latest_backup.txt)"
    echo ""
}

# Handle interrupts
trap 'error_exit "Script interrupted"' INT TERM

# Run main function
main "$@"
