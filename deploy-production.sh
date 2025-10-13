#!/bin/bash

# ================================================================
# ValueVerse Platform - Production Deployment Script
# ================================================================
# This script handles production deployments with safety checks,
# health monitoring, and automatic rollback on failure.
# ================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="valueverse"
ENVIRONMENT="production"
DEPLOYMENT_TIMEOUT=600  # 10 minutes
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

# ================================================================
# Pre-deployment Checks
# ================================================================

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed"
        exit 1
    fi
    
    # Check if required environment variables are set
    required_vars=(
        "DB_USERNAME"
        "DB_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET_KEY"
        "AWS_REGION"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    success "Prerequisites check passed"
}

# ================================================================
# Backup Current State
# ================================================================

backup_current_state() {
    log "Creating backup of current state..."
    
    BACKUP_DIR="./backups/pre-deployment-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    log "Backing up database..."
    docker-compose -f docker-compose.prod.yml exec -T postgres-primary \
        pg_dump -U "$DB_USERNAME" "$DB_NAME" | gzip > "$BACKUP_DIR/database.sql.gz"
    
    # Backup configuration
    log "Backing up configuration..."
    cp -r config "$BACKUP_DIR/"
    cp docker-compose.prod.yml "$BACKUP_DIR/"
    
    # Save current container states
    docker-compose -f docker-compose.prod.yml ps > "$BACKUP_DIR/container_states.txt"
    
    success "Backup completed: $BACKUP_DIR"
    echo "$BACKUP_DIR" > .last_backup_path
}

# ================================================================
# Database Migration
# ================================================================

run_migrations() {
    log "Running database migrations..."
    
    # Run migrations in a temporary container
    docker-compose -f docker-compose.prod.yml run --rm backend-1 \
        alembic upgrade head
    
    if [ $? -eq 0 ]; then
        success "Database migrations completed"
    else
        error "Database migrations failed"
        return 1
    fi
}

# ================================================================
# Blue-Green Deployment
# ================================================================

deploy_new_version() {
    log "Deploying new version..."
    
    # Pull latest images
    log "Pulling latest Docker images..."
    docker-compose -f docker-compose.prod.yml pull
    
    # Build custom images
    log "Building application images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start new containers alongside old ones
    log "Starting new containers..."
    docker-compose -f docker-compose.prod.yml up -d --no-deps --scale backend-1=6 backend-1
    
    # Wait for new containers to be healthy
    log "Waiting for new containers to be healthy..."
    wait_for_health
    
    if [ $? -eq 0 ]; then
        log "New containers are healthy, scaling down old containers..."
        docker-compose -f docker-compose.prod.yml up -d --no-deps --scale backend-1=3 backend-1
        success "Deployment completed"
    else
        error "New containers failed health check"
        return 1
    fi
}

# ================================================================
# Health Checks
# ================================================================

wait_for_health() {
    log "Performing health checks..."
    
    local retries=0
    local max_retries=$HEALTH_CHECK_RETRIES
    
    while [ $retries -lt $max_retries ]; do
        # Check backend health
        if curl -sf http://localhost/health > /dev/null 2>&1; then
            success "Backend is healthy"
            return 0
        fi
        
        retries=$((retries + 1))
        log "Health check attempt $retries/$max_retries..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    error "Health check failed after $max_retries attempts"
    return 1
}

check_service_health() {
    local service=$1
    log "Checking $service health..."
    
    case $service in
        "database")
            docker-compose -f docker-compose.prod.yml exec -T postgres-primary \
                pg_isready -U "$DB_USERNAME"
            ;;
        "redis")
            docker-compose -f docker-compose.prod.yml exec -T redis \
                redis-cli ping
            ;;
        "backend")
            curl -sf http://localhost/health
            ;;
        *)
            warning "Unknown service: $service"
            return 1
            ;;
    esac
}

# ================================================================
# Smoke Tests
# ================================================================

run_smoke_tests() {
    log "Running smoke tests..."
    
    # Test 1: API health endpoint
    log "Testing API health endpoint..."
    if ! curl -sf http://localhost/api/health > /dev/null; then
        error "API health check failed"
        return 1
    fi
    
    # Test 2: Database connectivity
    log "Testing database connectivity..."
    if ! check_service_health "database"; then
        error "Database connectivity test failed"
        return 1
    fi
    
    # Test 3: Redis connectivity
    log "Testing Redis connectivity..."
    if ! check_service_health "redis"; then
        error "Redis connectivity test failed"
        return 1
    fi
    
    # Test 4: Authentication endpoint
    log "Testing authentication endpoint..."
    if ! curl -sf -X POST http://localhost/api/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"test"}' > /dev/null; then
        warning "Auth endpoint test failed (expected, no test user)"
    fi
    
    success "Smoke tests passed"
}

# ================================================================
# Rollback
# ================================================================

rollback() {
    error "Deployment failed! Rolling back..."
    
    if [ ! -f .last_backup_path ]; then
        error "No backup path found, cannot rollback"
        exit 1
    fi
    
    BACKUP_PATH=$(cat .last_backup_path)
    
    log "Restoring from backup: $BACKUP_PATH"
    
    # Stop current containers
    docker-compose -f docker-compose.prod.yml down
    
    # Restore configuration
    cp -r "$BACKUP_PATH"/config/* ./config/
    cp "$BACKUP_PATH"/docker-compose.prod.yml ./
    
    # Restore database
    log "Restoring database..."
    gunzip < "$BACKUP_PATH/database.sql.gz" | \
        docker-compose -f docker-compose.prod.yml exec -T postgres-primary \
        psql -U "$DB_USERNAME" "$DB_NAME"
    
    # Restart services
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for health
    wait_for_health
    
    if [ $? -eq 0 ]; then
        success "Rollback completed successfully"
    else
        error "Rollback failed - manual intervention required!"
        exit 1
    fi
}

# ================================================================
# Post-deployment Tasks
# ================================================================

post_deployment_tasks() {
    log "Running post-deployment tasks..."
    
    # Clear application cache
    log "Clearing application cache..."
    docker-compose -f docker-compose.prod.yml exec -T redis \
        redis-cli FLUSHDB
    
    # Restart monitoring services
    log "Restarting monitoring services..."
    docker-compose -f docker-compose.prod.yml restart prometheus grafana
    
    # Send deployment notification
    send_notification "Deployment completed successfully"
    
    success "Post-deployment tasks completed"
}

# ================================================================
# Notifications
# ================================================================

send_notification() {
    local message=$1
    log "Notification: $message"
    
    # Send to Slack (example)
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"🚀 ValueVerse Deployment: $message\"}"
    fi
    
    # Send email (example)
    if [ -n "${NOTIFICATION_EMAIL:-}" ]; then
        echo "$message" | mail -s "ValueVerse Deployment" "$NOTIFICATION_EMAIL"
    fi
}

# ================================================================
# Main Deployment Flow
# ================================================================

main() {
    log "========================================="
    log "ValueVerse Production Deployment"
    log "========================================="
    log "Environment: $ENVIRONMENT"
    log "Timestamp: $(date)"
    log "========================================="
    
    # Confirm deployment
    read -p "Are you sure you want to deploy to PRODUCTION? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "Deployment cancelled"
        exit 0
    fi
    
    # Run deployment steps
    if ! check_prerequisites; then
        error "Prerequisites check failed"
        exit 1
    fi
    
    if ! backup_current_state; then
        error "Backup failed"
        exit 1
    fi
    
    if ! run_migrations; then
        error "Migrations failed"
        rollback
        exit 1
    fi
    
    if ! deploy_new_version; then
        error "Deployment failed"
        rollback
        exit 1
    fi
    
    if ! run_smoke_tests; then
        error "Smoke tests failed"
        rollback
        exit 1
    fi
    
    post_deployment_tasks
    
    log "========================================="
    success "🎉 Deployment completed successfully!"
    log "========================================="
    log "Next steps:"
    log "  1. Monitor application metrics"
    log "  2. Check error logs"
    log "  3. Verify user-facing features"
    log "========================================="
}

# Run main function
main "$@"
