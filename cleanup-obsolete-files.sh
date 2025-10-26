#!/bin/bash

# ============================================================================
# ValueVerse Repository Cleanup Script
# ============================================================================
# Removes obsolete, duplicate, and unnecessary files from the repository
# Creates a backup before deletion for safety
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/cleanup-backup-$(date +%Y%m%d_%H%M%S)"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be deleted without actually deleting"
            echo "  --help       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Banner
echo -e "${CYAN}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           ValueVerse Repository Cleanup                   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}🔍 DRY RUN MODE - No files will be deleted${NC}"
    echo ""
fi

# Files to remove (Phase 1 - Safe to delete)
declare -a FILES_TO_REMOVE=(
    # Duplicate configuration files
    "Makefile.complete"
    "deploy-local.sh"
    ".env.template"
    
    # Obsolete root documentation
    "README_DEPLOYMENT.md"
    "REORGANIZATION_SUMMARY.md"
    "COMPREHENSIVE_REPOSITORY_AUDIT.md"
    "DEPLOYMENT_VERIFICATION.md"
    "ai_development_summary.json"
    
    # Duplicate frontend files
    "frontend/app/page-enhanced.tsx"
    "frontend/utils.ts"
    
    # Temporary scripts
    "reorganize.sh"
    
    # Empty package lock
    "package-lock.json"
)

# Directories to remove
declare -a DIRS_TO_REMOVE=(
    "docs/archive"
)

# Function to create backup
create_backup() {
    local file=$1
    local backup_path="${BACKUP_DIR}/${file}"
    
    if [ -e "$file" ]; then
        mkdir -p "$(dirname "$backup_path")"
        cp -r "$file" "$backup_path"
        echo -e "${GREEN}  ✓ Backed up: ${file}${NC}"
    fi
}

# Function to remove file
remove_file() {
    local file=$1
    
    if [ -e "$file" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}  [DRY RUN] Would remove: ${file}${NC}"
        else
            rm -f "$file"
            echo -e "${GREEN}  ✓ Removed: ${file}${NC}"
        fi
        return 0
    else
        echo -e "${BLUE}  ℹ Skipped (not found): ${file}${NC}"
        return 1
    fi
}

# Function to remove directory
remove_directory() {
    local dir=$1
    
    if [ -d "$dir" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}  [DRY RUN] Would remove directory: ${dir}${NC}"
            find "$dir" -type f | head -5 | while read -r f; do
                echo -e "${YELLOW}    - $(basename "$f")${NC}"
            done
            local count=$(find "$dir" -type f | wc -l)
            if [ "$count" -gt 5 ]; then
                echo -e "${YELLOW}    ... and $((count - 5)) more files${NC}"
            fi
        else
            rm -rf "$dir"
            echo -e "${GREEN}  ✓ Removed directory: ${dir}${NC}"
        fi
        return 0
    else
        echo -e "${BLUE}  ℹ Skipped (not found): ${dir}${NC}"
        return 1
    fi
}

# Main execution
echo -e "${BLUE}📋 Cleanup Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Count files that exist
existing_files=0
existing_dirs=0

for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -e "$file" ]; then
        existing_files=$((existing_files + 1))
    fi
done

for dir in "${DIRS_TO_REMOVE[@]}"; do
    if [ -d "$dir" ]; then
        existing_dirs=$((existing_dirs + 1))
    fi
done

echo -e "${CYAN}Files to remove:${NC} ${existing_files}/${#FILES_TO_REMOVE[@]}"
echo -e "${CYAN}Directories to remove:${NC} ${existing_dirs}/${#DIRS_TO_REMOVE[@]}"
echo ""

if [ "$existing_files" -eq 0 ] && [ "$existing_dirs" -eq 0 ]; then
    echo -e "${GREEN}✓ Repository is already clean! No files to remove.${NC}"
    exit 0
fi

# Confirm unless dry run
if [ "$DRY_RUN" = false ]; then
    echo -e "${YELLOW}⚠️  This will permanently delete ${existing_files} files and ${existing_dirs} directories.${NC}"
    echo -e "${YELLOW}⚠️  A backup will be created at: ${BACKUP_DIR}${NC}"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Cleanup cancelled.${NC}"
        exit 0
    fi
    echo ""
fi

# Create backup directory
if [ "$DRY_RUN" = false ]; then
    mkdir -p "$BACKUP_DIR"
    echo -e "${BLUE}📦 Creating backup...${NC}"
    
    for file in "${FILES_TO_REMOVE[@]}"; do
        [ -e "$file" ] && create_backup "$file"
    done
    
    for dir in "${DIRS_TO_REMOVE[@]}"; do
        [ -d "$dir" ] && create_backup "$dir"
    done
    
    echo ""
fi

# Remove files
echo -e "${BLUE}🗑️  Removing duplicate configuration files...${NC}"
for file in "Makefile.complete" "deploy-local.sh" ".env.template" "package-lock.json"; do
    remove_file "$file"
done
echo ""

echo -e "${BLUE}🗑️  Removing obsolete root documentation...${NC}"
for file in "README_DEPLOYMENT.md" "REORGANIZATION_SUMMARY.md" "COMPREHENSIVE_REPOSITORY_AUDIT.md" "DEPLOYMENT_VERIFICATION.md" "ai_development_summary.json"; do
    remove_file "$file"
done
echo ""

echo -e "${BLUE}🗑️  Removing duplicate frontend files...${NC}"
for file in "frontend/app/page-enhanced.tsx" "frontend/utils.ts"; do
    remove_file "$file"
done
echo ""

echo -e "${BLUE}🗑️  Removing temporary scripts...${NC}"
remove_file "reorganize.sh"
echo ""

echo -e "${BLUE}🗑️  Removing archived documentation...${NC}"
for dir in "${DIRS_TO_REMOVE[@]}"; do
    remove_directory "$dir"
done
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}✓ Dry run complete! No files were actually deleted.${NC}"
    echo -e "${YELLOW}  Run without --dry-run to perform the cleanup.${NC}"
else
    echo -e "${GREEN}✓ Cleanup complete!${NC}"
    echo ""
    echo -e "${CYAN}Backup location:${NC} ${BACKUP_DIR}"
    echo -e "${CYAN}Backup size:${NC} $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo ""
    echo -e "${YELLOW}💡 To restore files if needed:${NC}"
    echo -e "   cp -r ${BACKUP_DIR}/* ."
    echo ""
    echo -e "${YELLOW}💡 To remove backup after verification:${NC}"
    echo -e "   rm -rf ${BACKUP_DIR}"
fi
echo ""

# Show what remains
echo -e "${BLUE}📊 Repository Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Active configuration files:${NC}"
echo "  ✓ Makefile"
echo "  ✓ deploy.sh"
echo "  ✓ .env.example"
echo "  ✓ docker-compose.complete.yml"
echo "  ✓ docker-compose.dev.yml"
echo "  ✓ docker-compose.prod.yml"
echo ""
echo -e "${CYAN}Active documentation:${NC}"
echo "  ✓ README.md"
echo "  ✓ CODEBASE_INDEX.md"
echo "  ✓ docs/ (without archive)"
echo ""
echo -e "${GREEN}✨ Repository is now cleaner and more maintainable!${NC}"
echo ""
