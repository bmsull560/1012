#!/bin/bash

# ValueVerse Repository Reorganization Script
# This script will reorganize the entire repository structure

set -e  # Exit on error

echo "🏗️  ValueVerse Repository Reorganization"
echo "========================================"
echo ""
echo "This will reorganize the entire repository structure."
echo "A backup will be created first."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Reorganization cancelled."
    exit 1
fi

# Create backup
echo "📦 Creating backup..."
BACKUP_NAME="backup_before_reorg_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf $BACKUP_NAME . \
  --exclude=node_modules \
  --exclude=.venv \
  --exclude=venv \
  --exclude=.git \
  --exclude=.next \
  --exclude=__pycache__ \
  --exclude=*.pyc 2>/dev/null || true

echo "✅ Backup created: $BACKUP_NAME"
echo ""

# Step 1: Create new directory structure
echo "📁 Creating new directory structure..."

# Infrastructure directories
mkdir -p infrastructure/docker
mkdir -p infrastructure/kubernetes/base
mkdir -p infrastructure/kubernetes/overlays
mkdir -p infrastructure/config/{nginx,prometheus,grafana}

# Scripts directories
mkdir -p scripts/setup
mkdir -p scripts/deploy
mkdir -p scripts/maintenance
mkdir -p scripts/testing

# Documentation directories
mkdir -p docs/architecture
mkdir -p docs/api
mkdir -p docs/deployment
mkdir -p docs/development
mkdir -p docs/archive

echo "✅ Directory structure created"
echo ""

# Step 2: Consolidate Backend
echo "🔧 Consolidating backend..."

# Check which backend is the production one
if [ -f "valueverse/backend/main.py" ]; then
    echo "  Moving production backend from valueverse/backend to backend/"
    
    # Create backend directory if it doesn't exist
    mkdir -p backend
    
    # Move everything from valueverse/backend to backend
    if [ -d "valueverse/backend/app" ]; then
        cp -r valueverse/backend/* backend/ 2>/dev/null || true
    fi
    
    # Move tests from src/backend if they exist
    if [ -d "src/backend/tests" ]; then
        cp -r src/backend/tests backend/ 2>/dev/null || true
    fi
    
    echo "  ✅ Backend consolidated"
else
    echo "  ⚠️  Production backend not found in expected location"
fi

# Step 3: Organize Infrastructure Files
echo "🏗️  Organizing infrastructure files..."

# Docker files
[ -f "docker-compose.yml" ] && mv docker-compose.yml infrastructure/docker/ 2>/dev/null || true
[ -f "docker-compose.prod.yml" ] && mv docker-compose.prod.yml infrastructure/docker/ 2>/dev/null || true
[ -f "docker-compose.dev.yml" ] && mv docker-compose.dev.yml infrastructure/docker/ 2>/dev/null || true
[ -f ".env.example" ] && cp .env.example infrastructure/docker/ 2>/dev/null || true

# Kubernetes files
if [ -d "kubernetes" ]; then
    cp -r kubernetes/* infrastructure/kubernetes/ 2>/dev/null || true
fi

# Config files
if [ -d "config" ]; then
    cp -r config/* infrastructure/config/ 2>/dev/null || true
fi

echo "✅ Infrastructure files organized"
echo ""

# Step 4: Organize Scripts
echo "📜 Organizing scripts..."

# Setup scripts
[ -f "setup-local.sh" ] && mv setup-local.sh scripts/setup/ 2>/dev/null || true
[ -f "quick-start.sh" ] && mv quick-start.sh scripts/setup/ 2>/dev/null || true

# Deploy scripts
[ -f "deploy.sh" ] && mv deploy.sh scripts/deploy/ 2>/dev/null || true
[ -f "deploy.ps1" ] && mv deploy.ps1 scripts/deploy/ 2>/dev/null || true
[ -f "deploy-production.sh" ] && mv deploy-production.sh scripts/deploy/ 2>/dev/null || true
[ -f "start.sh" ] && mv start.sh scripts/deploy/ 2>/dev/null || true
[ -f "run-frontend-only.sh" ] && mv run-frontend-only.sh scripts/deploy/ 2>/dev/null || true
[ -f "run-new-ui.sh" ] && mv run-new-ui.sh scripts/deploy/ 2>/dev/null || true
[ -f "docker-screenshot.sh" ] && mv docker-screenshot.sh scripts/deploy/ 2>/dev/null || true

# Maintenance scripts
[ -f "clean-cache.sh" ] && mv clean-cache.sh scripts/maintenance/ 2>/dev/null || true
[ -f "verify-deployment.sh" ] && mv verify-deployment.sh scripts/maintenance/ 2>/dev/null || true

# Testing scripts
[ -f "test-ui.js" ] && mv test-ui.js scripts/testing/ 2>/dev/null || true
[ -f "test-ui-complete.js" ] && mv test-ui-complete.js scripts/testing/ 2>/dev/null || true
[ -f "screenshot.js" ] && mv screenshot.js scripts/testing/ 2>/dev/null || true

echo "✅ Scripts organized"
echo ""

# Step 5: Consolidate Documentation
echo "📚 Consolidating documentation..."

# Architecture docs
for file in *ARCHITECTURE*.md *IMPLEMENTATION*.md *ANALYSIS*.md *AUDIT*.md; do
    [ -f "$file" ] && mv "$file" docs/architecture/ 2>/dev/null || true
done

# Deployment docs
for file in *DEPLOYMENT*.md *INFRASTRUCTURE*.md KUBERNETES*.md PRODUCTION*.md; do
    [ -f "$file" ] && mv "$file" docs/deployment/ 2>/dev/null || true
done

# Development docs
[ -f "CONTRIBUTING.md" ] && mv CONTRIBUTING.md docs/development/ 2>/dev/null || true
for file in *DEVELOPMENT*.md *ROADMAP*.md *PLAN*.md; do
    [ -f "$file" ] && mv "$file" docs/development/ 2>/dev/null || true
done

# Archive old status docs
for file in *STATUS*.md *COMPLETE*.md *SUCCESS*.md *FIXED*.md LAUNCH*.md FEATURES*.md; do
    [ -f "$file" ] && mv "$file" docs/archive/ 2>/dev/null || true
done

# Move misc docs
for file in *.md; do
    if [[ "$file" != "README.md" && "$file" != "REPOSITORY_REORGANIZATION_PLAN.md" ]]; then
        [ -f "$file" ] && mv "$file" docs/ 2>/dev/null || true
    fi
done

echo "✅ Documentation consolidated"
echo ""

# Step 6: Clean Up
echo "🧹 Cleaning up..."

# Remove empty/unnecessary directories
[ -d "archived_frontend" ] && rm -rf archived_frontend && echo "  Removed archived_frontend"
[ -d "src" ] && rm -rf src && echo "  Removed src directory"
[ -d "output" ] && rm -rf output && echo "  Removed output directory"
[ -d "tests" ] && [ -z "$(ls -A tests)" ] && rm -rf tests && echo "  Removed empty tests directory"
[ -d "node_modules" ] && rm -rf node_modules && echo "  Removed root node_modules"

# Remove old valueverse directory if backend was moved
if [ -d "backend/app" ] && [ -d "valueverse" ]; then
    rm -rf valueverse && echo "  Removed old valueverse directory"
fi

# Remove test files from root
[ -f "package.json" ] && [ -d "frontend/node_modules" ] && rm -f package*.json && echo "  Removed root package files"

# Remove HTML exports and screenshots
rm -f *.html 2>/dev/null && echo "  Removed HTML files"
rm -f *.png 2>/dev/null && echo "  Removed PNG files"

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
rm -rf .pytest_cache .ruff_cache 2>/dev/null || true

echo "✅ Cleanup complete"
echo ""

# Step 7: Create updated configuration files
echo "📝 Creating updated configuration files..."

# Create main .gitignore if not exists
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
.env
*.egg-info/
.pytest_cache/
.ruff_cache/

# Node
node_modules/
.next/
out/
build/
dist/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Docker
*.log
.docker/

# Secrets
*.pem
*.key
.env.local
.env.*.local

# Backups
backup_*.tar.gz
EOF

echo "✅ Configuration files updated"
echo ""

# Step 8: Update paths in Docker Compose
echo "🔧 Updating Docker Compose paths..."

if [ -f "infrastructure/docker/docker-compose.yml" ]; then
    # Update backend context path
    sed -i 's|context: \./src/backend|context: ../../backend|g' infrastructure/docker/docker-compose.yml 2>/dev/null || true
    sed -i 's|context: \.|context: ../..|g' infrastructure/docker/docker-compose.yml 2>/dev/null || true
    echo "  Updated docker-compose.yml"
fi

if [ -f "infrastructure/docker/docker-compose.prod.yml" ]; then
    # Update backend context path
    sed -i 's|context: \./valueverse/backend|context: ../../backend|g' infrastructure/docker/docker-compose.prod.yml 2>/dev/null || true
    sed -i 's|context: \./frontend|context: ../../frontend|g' infrastructure/docker/docker-compose.prod.yml 2>/dev/null || true
    echo "  Updated docker-compose.prod.yml"
fi

echo "✅ Docker Compose paths updated"
echo ""

# Final summary
echo "========================================="
echo "✅ Repository Reorganization Complete!"
echo "========================================="
echo ""
echo "📊 New Structure:"
echo ""
echo "valueverse/"
echo "├── backend/          # Production backend"
echo "├── frontend/         # Enhanced frontend"  
echo "├── infrastructure/   # Docker, K8s, configs"
echo "├── scripts/          # Organized scripts"
echo "├── docs/            # Consolidated docs"
echo "└── README.md        # Main documentation"
echo ""
echo "📝 Next Steps:"
echo "1. Review the new structure"
echo "2. Test backend: cd backend && python -m pytest"
echo "3. Test frontend: cd frontend && npm run dev"
echo "4. Test Docker: cd infrastructure/docker && docker-compose up"
echo ""
echo "💾 Backup saved as: $BACKUP_NAME"
echo ""
echo "🎉 Your repository is now clean and organized!"
