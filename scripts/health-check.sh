#!/bin/bash

# ============================================================================
# ValueVerse Platform - Health Check Script
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Service configuration
declare -A services=(
    ["PostgreSQL"]="5432"
    ["Redis"]="6379"
    ["RabbitMQ Management"]="15672"
    ["Kong Gateway"]="8000"
    ["Kong Admin"]="8001"
    ["Consul"]="8500"
    ["Jaeger"]="16686"
    ["Prometheus"]="9090"
    ["Grafana"]="3001"
    ["Value Architect"]="8011"
    ["Value Committer"]="8012"
    ["Value Executor"]="8013"
    ["Value Amplifier"]="8014"
    ["Calculation Engine"]="8015"
    ["Notification Service"]="8016"
    ["Frontend"]="3000"
)

# Counters
healthy=0
unhealthy=0
total=0

# Show header
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           ValueVerse Platform Health Check               ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Checking service health...${NC}"
echo "─────────────────────────────────────────────────────────"

# Function to check service health
check_service() {
    local name=$1
    local port=$2
    local url=""
    local status=""
    
    # Determine health check endpoint
    case $port in
        5432)  # PostgreSQL
            docker exec valueverse-postgres pg_isready -U postgres >/dev/null 2>&1 && status="healthy" || status="unhealthy"
            ;;
        6379)  # Redis
            docker exec valueverse-redis redis-cli ping >/dev/null 2>&1 && status="healthy" || status="unhealthy"
            ;;
        8011|8012|8013|8014|8015|8016)  # Microservices
            url="http://localhost:${port}/health"
            curl -sf "$url" >/dev/null 2>&1 && status="healthy" || status="unhealthy"
            ;;
        *)  # Other HTTP services
            url="http://localhost:${port}"
            curl -sf "$url" >/dev/null 2>&1 && status="healthy" || status="unhealthy"
            ;;
    esac
    
    # Display result
    printf "%-25s [%4s]  " "$name" "$port"
    
    if [ "$status" = "healthy" ]; then
        echo -e "${GREEN}✓ Healthy${NC}"
        ((healthy++))
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        ((unhealthy++))
    fi
    
    ((total++))
}

# Check each service
for service_name in "${!services[@]}"; do
    port="${services[$service_name]}"
    check_service "$service_name" "$port"
done

echo "─────────────────────────────────────────────────────────"

# Show summary
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  Total Services:    $total"
echo -e "  ${GREEN}Healthy:${NC}          $healthy"
echo -e "  ${RED}Unhealthy:${NC}        $unhealthy"

# Calculate health percentage
if [ $total -gt 0 ]; then
    health_percent=$((healthy * 100 / total))
    echo -e "  Health Score:      ${health_percent}%"
    
    # Show overall status
    echo ""
    if [ $health_percent -eq 100 ]; then
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}     ✓ All services are healthy! Platform is ready.       ${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        exit 0
    elif [ $health_percent -ge 80 ]; then
        echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}     ⚠ Most services are healthy. Check failed services.  ${NC}"
        echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
        exit 1
    else
        echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}     ✗ Multiple services are down. Deployment may have failed.${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
        exit 2
    fi
fi

# Additional diagnostics if services are unhealthy
if [ $unhealthy -gt 0 ]; then
    echo ""
    echo -e "${BLUE}Diagnostic Information:${NC}"
    echo "─────────────────────────────────────────────────────────"
    
    # Check Docker
    echo -n "Docker Status:         "
    if docker info >/dev/null 2>&1; then
        echo -e "${GREEN}Running${NC}"
    else
        echo -e "${RED}Not Running${NC}"
    fi
    
    # Check containers
    echo -n "Running Containers:    "
    container_count=$(docker ps -q | wc -l)
    echo "$container_count"
    
    # Check disk space
    echo -n "Available Disk Space:  "
    df -h . | awk 'NR==2{print $4}'
    
    # Check memory
    echo -n "Available Memory:      "
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        free -h | awk 'NR==2{print $7}'
    else
        echo "N/A"
    fi
    
    echo ""
    echo -e "${BLUE}Troubleshooting Steps:${NC}"
    echo "1. Check logs:     docker compose logs [service-name]"
    echo "2. Restart failed: docker compose restart [service-name]"
    echo "3. Full restart:   ./deploy.sh restart"
    echo "4. Check ports:    lsof -i :[port-number]"
fi
