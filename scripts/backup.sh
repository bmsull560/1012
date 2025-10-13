#!/bin/bash

# ============================================================================
# ValueVerse Platform - Backup Script
# ============================================================================

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PREFIX="valueverse_backup"
RETENTION_DAYS=30

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Backup types
BACKUP_TYPE="${1:-full}"

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

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log "Created backup directory: $BACKUP_DIR"
    fi
}

# Backup database
backup_database() {
    log "Starting database backup..."
    
    local db_backup_file="$BACKUP_DIR/${BACKUP_PREFIX}_db_${TIMESTAMP}.sql"
    
    # Check if PostgreSQL container is running
    if docker ps | grep -q valueverse-postgres; then
        docker exec valueverse-postgres pg_dumpall -U postgres > "$db_backup_file" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            # Compress the backup
            gzip "$db_backup_file"
            success "Database backed up to: ${db_backup_file}.gz"
            echo "${db_backup_file}.gz"
        else
            error "Failed to backup database"
        fi
    else
        warning "PostgreSQL container is not running"
        echo ""
    fi
}

# Backup Redis
backup_redis() {
    log "Starting Redis backup..."
    
    local redis_backup_file="$BACKUP_DIR/${BACKUP_PREFIX}_redis_${TIMESTAMP}.rdb"
    
    if docker ps | grep -q valueverse-redis; then
        # Trigger Redis save
        docker exec valueverse-redis redis-cli BGSAVE >/dev/null 2>&1
        sleep 2
        
        # Copy dump file
        docker cp valueverse-redis:/data/dump.rdb "$redis_backup_file" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            # Compress the backup
            gzip "$redis_backup_file"
            success "Redis backed up to: ${redis_backup_file}.gz"
            echo "${redis_backup_file}.gz"
        else
            warning "Failed to backup Redis"
            echo ""
        fi
    else
        warning "Redis container is not running"
        echo ""
    fi
}

# Backup volumes
backup_volumes() {
    log "Starting Docker volumes backup..."
    
    local volumes_backup_file="$BACKUP_DIR/${BACKUP_PREFIX}_volumes_${TIMESTAMP}.tar.gz"
    
    # Get all volumes for the project
    volumes=$(docker volume ls -q | grep -E "^(valueverse|services|infrastructure|frontend)" || true)
    
    if [ ! -z "$volumes" ]; then
        # Create temporary container to access volumes
        docker run --rm \
            $(echo $volumes | xargs -n1 printf -- "-v %s:/backup/%s ") \
            alpine tar czf - -C /backup . > "$volumes_backup_file" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            success "Volumes backed up to: $volumes_backup_file"
            echo "$volumes_backup_file"
        else
            warning "Failed to backup volumes"
            echo ""
        fi
    else
        warning "No volumes found to backup"
        echo ""
    fi
}

# Backup configuration files
backup_configs() {
    log "Starting configuration backup..."
    
    local config_backup_file="$BACKUP_DIR/${BACKUP_PREFIX}_configs_${TIMESTAMP}.tar.gz"
    
    # Files and directories to backup
    local config_items=(
        ".env"
        "docker-compose*.yml"
        "Makefile*"
        "scripts/"
        "infrastructure/"
        "frontend/.env*"
        "frontend/package.json"
        "services/*/requirements.txt"
        "services/*/package.json"
    )
    
    # Create tar with configs
    tar czf "$config_backup_file" \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='*.pyc' \
        ${config_items[@]} 2>/dev/null || true
    
    if [ -f "$config_backup_file" ]; then
        success "Configurations backed up to: $config_backup_file"
        echo "$config_backup_file"
    else
        warning "Failed to backup configurations"
        echo ""
    fi
}

# Backup application data
backup_application() {
    log "Starting application data backup..."
    
    local app_backup_file="$BACKUP_DIR/${BACKUP_PREFIX}_app_${TIMESTAMP}.tar.gz"
    
    # Directories to backup
    local app_dirs=(
        "frontend/app"
        "frontend/components"
        "frontend/public"
        "services/value-architect"
        "services/value-committer"
        "services/value-executor"
        "services/value-amplifier"
        "billing-system"
    )
    
    # Create tar with application files
    tar czf "$app_backup_file" \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.next' \
        --exclude='dist' \
        --exclude='build' \
        --exclude='*.pyc' \
        ${app_dirs[@]} 2>/dev/null || true
    
    if [ -f "$app_backup_file" ]; then
        success "Application data backed up to: $app_backup_file"
        echo "$app_backup_file"
    else
        warning "Failed to backup application data"
        echo ""
    fi
}

# Create backup manifest
create_manifest() {
    local backup_files=("$@")
    local manifest_file="$BACKUP_DIR/${BACKUP_PREFIX}_manifest_${TIMESTAMP}.json"
    
    cat > "$manifest_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "type": "$BACKUP_TYPE",
    "platform_version": "1.0.0",
    "files": [
EOF
    
    local first=true
    for file in "${backup_files[@]}"; do
        if [ ! -z "$file" ] && [ -f "$file" ]; then
            if [ "$first" = false ]; then
                echo "," >> "$manifest_file"
            fi
            echo -n "        {
            \"file\": \"$(basename $file)\",
            \"size\": \"$(du -h $file | cut -f1)\",
            \"md5\": \"$(md5sum $file | cut -d' ' -f1 2>/dev/null || echo 'N/A')\"
        }" >> "$manifest_file"
            first=false
        fi
    done
    
    cat >> "$manifest_file" << EOF

    ],
    "total_size": "$(du -sh $BACKUP_DIR | cut -f1)"
}
EOF
    
    success "Manifest created: $manifest_file"
}

# Clean old backups
clean_old_backups() {
    log "Cleaning old backups (older than $RETENTION_DAYS days)..."
    
    find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    success "Old backups cleaned"
}

# Main backup process
main() {
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           ValueVerse Platform Backup Utility             ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    log "Starting backup process (Type: $BACKUP_TYPE)"
    
    # Create backup directory
    create_backup_dir
    
    # Array to store backup files
    backup_files=()
    
    # Perform backups based on type
    case $BACKUP_TYPE in
        full)
            backup_files+=("$(backup_database)")
            backup_files+=("$(backup_redis)")
            backup_files+=("$(backup_volumes)")
            backup_files+=("$(backup_configs)")
            backup_files+=("$(backup_application)")
            ;;
        database)
            backup_files+=("$(backup_database)")
            backup_files+=("$(backup_redis)")
            ;;
        volumes)
            backup_files+=("$(backup_volumes)")
            ;;
        configs)
            backup_files+=("$(backup_configs)")
            ;;
        application)
            backup_files+=("$(backup_application)")
            ;;
        state)
            backup_files+=("$(backup_database)")
            backup_files+=("$(backup_redis)")
            backup_files+=("$(backup_configs)")
            ;;
        *)
            error "Unknown backup type: $BACKUP_TYPE"
            ;;
    esac
    
    # Create manifest
    create_manifest "${backup_files[@]}"
    
    # Clean old backups
    if [ "$CLEAN_OLD" = "true" ]; then
        clean_old_backups
    fi
    
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           ✓ Backup completed successfully!                ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Backup location: $BACKUP_DIR"
    echo "Timestamp: $TIMESTAMP"
    echo ""
    echo "To restore from this backup, run:"
    echo "  ./scripts/restore.sh $BACKUP_DIR $TIMESTAMP"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --clean)
            CLEAN_OLD="true"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [backup-type] [options]"
            echo ""
            echo "Backup types:"
            echo "  full         - Complete backup (default)"
            echo "  database     - Database and Redis only"
            echo "  volumes      - Docker volumes only"
            echo "  configs      - Configuration files only"
            echo "  application  - Application code only"
            echo "  state        - Database, Redis, and configs"
            echo ""
            echo "Options:"
            echo "  --dir DIR        - Backup directory (default: ./backups)"
            echo "  --retention DAYS - Days to retain old backups (default: 30)"
            echo "  --clean          - Clean old backups"
            echo "  -h, --help       - Show this help"
            exit 0
            ;;
        *)
            BACKUP_TYPE="$1"
            shift
            ;;
    esac
done

# Run main function
main
