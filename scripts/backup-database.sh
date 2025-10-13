#!/bin/bash

# ================================================================
# Database Backup Script for ValueVerse Platform
# ================================================================
# Features:
# - Automated hourly/daily backups
# - Compression and encryption
# - S3 upload with versioning
# - Retention policy management
# - Backup verification
# ================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/backups/database}"
S3_BUCKET="${S3_BACKUP_BUCKET:-valueverse-backups}"
DB_HOST="${DB_HOST:-postgres-primary}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USERNAME}"
DB_NAME="${DB_NAME:-valueverse}"
ENCRYPTION_KEY_FILE="${ENCRYPTION_KEY_FILE:-/etc/valueverse/backup-key.aes}"

# Retention settings
HOURLY_RETENTION_DAYS=7
DAILY_RETENTION_DAYS=30
WEEKLY_RETENTION_WEEKS=12
MONTHLY_RETENTION_MONTHS=12

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }

# ================================================================
# Backup Functions
# ================================================================

create_backup() {
    local backup_type=$1  # hourly, daily, weekly, monthly
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/${backup_type}/valueverse_${backup_type}_${timestamp}.sql"
    local compressed_file="${backup_file}.gz"
    local encrypted_file="${compressed_file}.enc"
    
    log "Starting ${backup_type} backup..."
    
    # Create backup directory
    mkdir -p "${BACKUP_DIR}/${backup_type}"
    
    # Perform database dump
    log "Dumping database..."
    if ! PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=custom \
        --compress=0 \
        --verbose \
        --file="$backup_file" 2>&1 | tee -a "${BACKUP_DIR}/backup.log"; then
        error "Database dump failed"
        return 1
    fi
    
    # Compress backup
    log "Compressing backup..."
    if ! gzip -9 "$backup_file"; then
        error "Compression failed"
        return 1
    fi
    
    # Encrypt backup (if encryption key exists)
    if [ -f "$ENCRYPTION_KEY_FILE" ]; then
        log "Encrypting backup..."
        if ! openssl enc -aes-256-cbc \
            -salt \
            -in "$compressed_file" \
            -out "$encrypted_file" \
            -pass file:"$ENCRYPTION_KEY_FILE"; then
            error "Encryption failed"
            return 1
        fi
        rm "$compressed_file"
        compressed_file="$encrypted_file"
    fi
    
    # Calculate checksum
    local checksum=$(sha256sum "$compressed_file" | awk '{print $1}')
    echo "$checksum" > "${compressed_file}.sha256"
    
    # Get backup size
    local backup_size=$(du -h "$compressed_file" | cut -f1)
    
    success "Backup created: $compressed_file ($backup_size)"
    
    # Upload to S3
    if command -v aws &> /dev/null; then
        upload_to_s3 "$compressed_file" "$backup_type"
    else
        warning "AWS CLI not found, skipping S3 upload"
    fi
    
    # Verify backup
    verify_backup "$compressed_file"
    
    # Update metadata
    update_backup_metadata "$backup_type" "$compressed_file" "$checksum" "$backup_size"
    
    # Cleanup old backups
    cleanup_old_backups "$backup_type"
}

# ================================================================
# S3 Upload
# ================================================================

upload_to_s3() {
    local file=$1
    local backup_type=$2
    
    log "Uploading to S3..."
    
    local s3_path="s3://${S3_BUCKET}/database/${backup_type}/$(basename $file)"
    
    if aws s3 cp "$file" "$s3_path" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256 \
        --metadata "backup-type=${backup_type},created=$(date -Iseconds)"; then
        success "Uploaded to S3: $s3_path"
        
        # Upload checksum
        aws s3 cp "${file}.sha256" "${s3_path}.sha256" \
            --storage-class STANDARD_IA
    else
        error "S3 upload failed"
        return 1
    fi
}

# ================================================================
# Backup Verification
# ================================================================

verify_backup() {
    local backup_file=$1
    
    log "Verifying backup integrity..."
    
    # Verify checksum
    if [ -f "${backup_file}.sha256" ]; then
        local expected_checksum=$(cat "${backup_file}.sha256")
        local actual_checksum=$(sha256sum "$backup_file" | awk '{print $1}')
        
        if [ "$expected_checksum" = "$actual_checksum" ]; then
            success "Checksum verification passed"
        else
            error "Checksum verification failed!"
            return 1
        fi
    fi
    
    # Test restore (to temporary database)
    log "Testing backup restore..."
    local test_db="test_restore_$$"
    
    # Decrypt if needed
    local restore_file="$backup_file"
    if [[ $backup_file == *.enc ]]; then
        local decrypted_file="${backup_file%.enc}"
        openssl enc -aes-256-cbc -d \
            -in "$backup_file" \
            -out "$decrypted_file" \
            -pass file:"$ENCRYPTION_KEY_FILE"
        restore_file="$decrypted_file"
    fi
    
    # Decompress
    if [[ $restore_file == *.gz ]]; then
        local uncompressed_file="${restore_file%.gz}"
        gunzip -c "$restore_file" > "$uncompressed_file"
        restore_file="$uncompressed_file"
    fi
    
    # Create test database
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $test_db"
    
    # Restore backup to test database
    if PGPASSWORD="$DB_PASSWORD" pg_restore \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$test_db" \
        --no-owner \
        --no-acl \
        "$restore_file" 2>&1 | tee -a "${BACKUP_DIR}/verify.log"; then
        success "Backup restore test passed"
    else
        error "Backup restore test failed"
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $test_db"
        return 1
    fi
    
    # Cleanup test database
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE $test_db"
    
    # Cleanup temporary files
    [[ $restore_file != $backup_file ]] && rm -f "$restore_file"
}

# ================================================================
# Metadata Management
# ================================================================

update_backup_metadata() {
    local backup_type=$1
    local file=$2
    local checksum=$3
    local size=$4
    
    local metadata_file="${BACKUP_DIR}/backup-metadata.json"
    
    # Create metadata entry
    local entry=$(cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "type": "$backup_type",
  "file": "$file",
  "checksum": "$checksum",
  "size": "$size",
  "database": "$DB_NAME",
  "host": "$DB_HOST"
}
EOF
)
    
    # Append to metadata file
    if [ -f "$metadata_file" ]; then
        # Parse existing JSON and add new entry
        jq ". += [$entry]" "$metadata_file" > "${metadata_file}.tmp" && \
            mv "${metadata_file}.tmp" "$metadata_file"
    else
        echo "[$entry]" > "$metadata_file"
    fi
    
    # Send metrics to Prometheus (if pushgateway is available)
    if command -v curl &> /dev/null && [ -n "${PUSHGATEWAY_URL:-}" ]; then
        cat <<EOF | curl --data-binary @- "${PUSHGATEWAY_URL}/metrics/job/backup"
# TYPE backup_size_bytes gauge
backup_size_bytes{type="$backup_type"} $(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
# TYPE backup_duration_seconds gauge
backup_duration_seconds{type="$backup_type"} $SECONDS
# TYPE backup_last_success_timestamp_seconds gauge
backup_last_success_timestamp_seconds{type="$backup_type"} $(date +%s)
EOF
    fi
}

# ================================================================
# Retention Management
# ================================================================

cleanup_old_backups() {
    local backup_type=$1
    
    log "Cleaning up old ${backup_type} backups..."
    
    local retention_days
    case $backup_type in
        hourly) retention_days=$HOURLY_RETENTION_DAYS ;;
        daily) retention_days=$DAILY_RETENTION_DAYS ;;
        weekly) retention_days=$((WEEKLY_RETENTION_WEEKS * 7)) ;;
        monthly) retention_days=$((MONTHLY_RETENTION_MONTHS * 30)) ;;
        *) retention_days=7 ;;
    esac
    
    # Delete local backups older than retention period
    find "${BACKUP_DIR}/${backup_type}" -name "valueverse_${backup_type}_*.sql.gz*" \
        -mtime +$retention_days -delete
    
    log "Deleted backups older than ${retention_days} days"
    
    # Delete old S3 backups
    if command -v aws &> /dev/null; then
        local cutoff_date=$(date -d "${retention_days} days ago" +%Y-%m-%d)
        aws s3 ls "s3://${S3_BUCKET}/database/${backup_type}/" | \
            awk '{print $4}' | \
            while read file; do
                local file_date=$(echo "$file" | grep -oP '\d{8}' | head -1)
                if [ "$file_date" \< "${cutoff_date//-/}" ]; then
                    aws s3 rm "s3://${S3_BUCKET}/database/${backup_type}/${file}"
                    log "Deleted S3 backup: $file"
                fi
            done
    fi
}

# ================================================================
# Main Function
# ================================================================

main() {
    log "========================================="
    log "ValueVerse Database Backup"
    log "========================================="
    
    # Determine backup type based on time
    local hour=$(date +%H)
    local day_of_week=$(date +%u)
    local day_of_month=$(date +%d)
    
    local backup_type="hourly"
    
    # Monthly backup on 1st of month at midnight
    if [ "$day_of_month" = "01" ] && [ "$hour" = "00" ]; then
        backup_type="monthly"
    # Weekly backup on Sunday at midnight
    elif [ "$day_of_week" = "7" ] && [ "$hour" = "00" ]; then
        backup_type="weekly"
    # Daily backup at midnight
    elif [ "$hour" = "00" ]; then
        backup_type="daily"
    fi
    
    log "Backup type: $backup_type"
    
    # Create backup
    if create_backup "$backup_type"; then
        success "Backup completed successfully"
        exit 0
    else
        error "Backup failed"
        
        # Send alert
        if [ -n "${ALERT_EMAIL:-}" ]; then
            echo "Database backup failed at $(date)" | \
                mail -s "CRITICAL: ValueVerse Backup Failed" "$ALERT_EMAIL"
        fi
        
        exit 1
    fi
}

# Run main function
main "$@"
