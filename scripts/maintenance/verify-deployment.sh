#!/bin/bash
# Deployment Verification Script

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Deployment Verification Check       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check files exist
echo -e "${BLUE}→ Checking deployment files...${NC}"
files=("Makefile" "deploy.sh" "deploy.ps1" "docker-compose.yml" ".env.example" "DEPLOYMENT.md" "QUICK_START.md")
missing=0

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (missing)"
        missing=$((missing + 1))
    fi
done

if [ $missing -eq 0 ]; then
    echo -e "${GREEN}✓ All deployment files present${NC}"
else
    echo -e "${YELLOW}⚠ $missing file(s) missing${NC}"
fi
echo ""

# Check dependencies
echo -e "${BLUE}→ Checking dependencies...${NC}"

if command -v docker >/dev/null 2>&1; then
    docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "  ${GREEN}✓${NC} Docker ($docker_version)"
else
    echo -e "  ${RED}✗${NC} Docker (not installed)"
fi

if command -v docker-compose >/dev/null 2>&1; then
    compose_version=$(docker-compose --version | cut -d' ' -f4 | cut -d',' -f1)
    echo -e "  ${GREEN}✓${NC} Docker Compose ($compose_version)"
elif docker compose version >/dev/null 2>&1; then
    compose_version=$(docker compose version | cut -d' ' -f4 | cut -d',' -f1)
    echo -e "  ${GREEN}✓${NC} Docker Compose ($compose_version)"
else
    echo -e "  ${RED}✗${NC} Docker Compose (not installed)"
fi

if command -v make >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Make"
else
    echo -e "  ${YELLOW}⚠${NC} Make (optional, can use ./deploy.sh instead)"
fi

if docker info >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Docker daemon running"
else
    echo -e "  ${RED}✗${NC} Docker daemon not running"
fi
echo ""

# Check permissions
echo -e "${BLUE}→ Checking script permissions...${NC}"
if [ -x "deploy.sh" ]; then
    echo -e "  ${GREEN}✓${NC} deploy.sh is executable"
else
    echo -e "  ${YELLOW}⚠${NC} deploy.sh not executable (run: chmod +x deploy.sh)"
fi
echo ""

# Check Docker resources
echo -e "${BLUE}→ Checking Docker resources...${NC}"
if docker info >/dev/null 2>&1; then
    # Get available disk space
    disk_space=$(df -h . | awk 'NR==2 {print $4}')
    echo -e "  ${GREEN}✓${NC} Disk space available: $disk_space"
    
    # Note: Docker memory info requires additional tools
    echo -e "  ${BLUE}ℹ${NC} Recommended: 4GB+ RAM, 10GB+ disk"
fi
echo ""

# Final verdict
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Verification Result          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

if [ $missing -eq 0 ] && command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✓ System is ready for deployment!${NC}"
    echo ""
    echo -e "${BLUE}To deploy, run:${NC}"
    echo "  make deploy"
    echo "  OR"
    echo "  ./deploy.sh"
    echo ""
else
    echo -e "${YELLOW}⚠ Some requirements are missing${NC}"
    echo ""
    echo "Please ensure:"
    echo "  1. Docker Desktop is installed and running"
    echo "  2. All deployment files are present"
    echo "  3. deploy.sh is executable (chmod +x deploy.sh)"
    echo ""
fi
