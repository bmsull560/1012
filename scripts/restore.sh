#!/bin/bash

# ============================================================================
# ValueVerse Platform - Restore Script
# ============================================================================

set -e

# Configuration
BACKUP_DIR="${1:-./backups}"
TIMESTAMP="${2:-latest}"
RESTORE_TYPE="${3:-full}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Find latest backup if not specified
find_backup() {
    if [ "$TIMESTAMP" = "latest" ]; then
        # Find the latest manifest
        MANIFEST=$(ls -t "$BACKUP_DIR"/valueverse_backup_manifest_*.json 2>/dev/null | head -1)
        if [ -z "$MANIFEST" ]; then
            error "No backup found in $BACKUP_DIR"
        fi
        TIMESTAMP=$(basename "$MANIFEST" | sed 's/valueverse_backup_manifest_//;s/.json//')
        log "Using latest backup: $TIMESTAMP"
    else
        MANIFEST="$BACKUP_DIR/valueverse_backup_manifest_${TIMESTAMP}.json"
        if [ ! -f "$MANIFEST" ]; then
            error "Backup manifest not found: $MANIFEST"
        fi
    fi
}

# Stop services
stop_services() {
    log "Stopping all services..."
    
    docker compose -f docker-compose.complete.yml down 2>/dev/null || true
    
    success "Services stopped"
}

# Restore database
restore_database() {
    local db_backup="$BACKUP_DIR/valueverse_backup_db_${TIMESTAMP}.sql.gz"
    
    if [ -f "$db_backup" ]; then
        log "Restoring database from: $db_backup"
        
        # Start PostgreSQL if not running
        docker compose -f docker-compose.complete.yml up -d postgres
        sleep 10
        
        # Drop and recreate database
        docker exec valueverse-postgres psql -U postgres -c "DROP DATABASE IF EXISTS valueverse;" 2>/dev/null || true
        docker exec valueverse-postgres psql -U postgres -c "CREATE DATABASE valueverse;" 2>/dev/null || true
        
        # Restore backup
        gunzip -c "$db_backup" | docker exec -i valueverse-postgres psql -U postgres 2>/dev/null
        
        if [ $? -eq 0 ]; then
            success "Database restored successfully"
        else
            error "Failed to restore database"
        fi
    else
        warning "Database backup not found: $db_backup"
    fi
}

# Restore Redis
restore_redis() {
    local redis_backup="$BACKUP_DIR/valueverse_backup_redis_${TIMESTAMP}.rdb.gz"
    
    if [ -f "$redis_backup" ]; then
        log "Restoring Redis from: $redis_backup"
        
        # Stop Redis if running
        docker compose -f docker-compose.complete.yml stop redis 2>/dev/null || true
        
        # Extract and copy dump file
        gunzip -c "$redis_backup" > /tmp/dump.rdb
        
        # Start Redis container
        docker compose -f docker-compose.complete.yml up -d redis
        sleep 5
        
        # Copy dump file to container
        docker cp /tmp/dump.rdb valueverse-redis:/data/dump.rdb
        
        # Restart Redis to load dump
        docker compose -f docker-compose.complete.yml restart redis
        
        # Clean up
        rm -f /tmp/dump.rdb
        
        success "Redis restored successfully"
    else
        warning "Redis backup not found: $redis_backup"
    fi
}

# Restore volumes
restore_volumes() {
    local volumes_backup="$BACKUP_DIR/valueverse_backup_volumes_${TIMESTAMP}.tar.gz"
    
    if [ -f "$volumes_backup" ]; then
        log "Restoring Docker volumes from: $volumes_backup"
        
        # Remove existing volumes
        docker volume ls -q | grep -E "^(valueverse|services|infrastructure|frontend)" | xargs -r docker volume rm -f 2>/dev/null || true
        
        # Create new volumes
        volumes=$(tar tzf "$volumes_backup" | cut -d/ -f1 | sort -u)
        for vol in $volumes; do
            docker volume create $vol 2>/dev/null || true
        done
        
        # Restore volume data
        docker run --rm \
            $(echo $volumes | xargs -n1 printf -- "-v %s:/backup/%s ") \
            -v "$volumes_backup:/restore.tar.gz:ro" \
            alpine sh -c "cd /backup && tar xzf /restore.tar.gz"
        
        if [ $? -eq 0 ]; then
            success "Volumes restored successfully"
        else
            warning "Failed to restore some volumes"
        fi
    else
        warning "Volumes backup not found: $volumes_backup"
    fi
}

# Restore configurations
restore_configs() {
    local config_backup="$BACKUP_DIR/valueverse_backup_configs_${TIMESTAMP}.tar.gz"
    
    if [ -f "$config_backup" ]; then
        log "Restoring configurations from: $config_backup"
        
        # Create backup of current configs
        mv .env .env.bak 2>/dev/null || true
        
        # Extract configurations
        tar xzf "$config_backup" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            success "Configurations restored successfully"
        else
            warning "Failed to restore some configurations"
        fi
    else
        warning "Configuration backup not found: $config_backup"
    fi
}

# Restore application
restore_application() {
    local app_backup="$BACKUP_DIR/valueverse_backup_app_${TIMESTAMP}.tar.gz"
    
    if [ -f "$app_backup" ]; then
        log "Restoring application data from: $app_backup"
        
        # Extract application files
        tar xzf "$app_backup" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            success "Application data restored successfully"
        else
            warning "Failed to restore some application data"
        fi
    else
        warning "Application backup not found: $app_backup"
    fi
}

# Start services
start_services() {
    log "Starting all services..."
    
    # Start infrastructure first
    docker compose -f docker-compose.complete.yml up -d postgres redis rabbitmq
    sleep 10
    
    # Start remaining services
    docker compose -f docker-compose.complete.yml up -d
    
    success "Services started"
}

# Verify restore
verify_restore() {
    log "Verifying restore..."
    
    # Wait for services to be ready
    sleep 30
    
    # Run health check
    ./scripts/health-check.sh
}

# Main restore process
main() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           ValueVerse Platform Restore Utility            ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Find backup
    find_backup
    
    log "Starting restore process"
    log "Backup directory: $BACKUP_DIR"
    log "Timestamp: $TIMESTAMP"
    log "Restore type: $RESTORE_TYPE"
    echo ""
    
    # Confirm restore
    echo -e "${YELLOW}WARNING: This will overwrite existing data!${NC}"
    read -p "Are you sure you want to restore? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "Restore cancelled"
        exit 0
    fi
    
    # Stop services
    stop_services
    
    # Perform restore based on type
    case $RESTORE_TYPE in
        full)
            restore_database
            restore_redis
            restore_volumes
            restore_configs
            restore_application
            ;;
        database)
            restore_database
            restore_redis
            ;;
        volumes)
            restore_volumes
            ;;
        configs)
            restore_configs
            ;;
        application)
            restore_application
            ;;
        state)
            restore_database
            restore_redis
            restore_configs
            ;;
        *)
            error "Unknown restore type: $RESTORE_TYPE"
            ;;
    esac
    
    # Start services
    start_services
    
    # Verify restore
    verify_restore
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           ✓ Restore completed successfully!               ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Restored from backup: $TIMESTAMP"
    echo ""
    echo "Access points:"
    echo "  Main Application: http://localhost:3000"
    echo "  API Gateway:      http://localhost:8000"
    echo "  Grafana:          http://localhost:3001"
}

# Parse arguments
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage: $0 [backup-dir] [timestamp] [restore-type]"
    echo ""
    echo "Arguments:"
    echo "  backup-dir   - Directory containing backups (default: ./backups)"
    echo "  timestamp    - Backup timestamp or 'latest' (default: latest)"
    echo "  restore-type - Type of restore to perform (default: full)"
    echo ""
    echo "Restore types:"
    echo "  full        - Complete restore"
    echo "  database    - Database and Redis only"
    echo "  volumes     - Docker volumes only"
    echo "  configs     - Configuration files only"
    echo "  application - Application code only"
    echo "  state       - Database, Redis, and configs"
    echo ""
    echo "Examples:"
    echo "  $0                           # Restore latest full backup"
    echo "  $0 ./backups latest database # Restore latest database backup"
    echo "  $0 ./backups 20240115_120000 full # Restore specific backup"
    exit 0
fi

# Run main function
main
