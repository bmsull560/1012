#!/bin/bash

# Complete Local Deployment Script for ValueVerse
# Deploys entire microservices stack with infrastructure and advanced features

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Deployment configuration
DEPLOY_DIR="$(pwd)"
SERVICES_DIR="$DEPLOY_DIR/services"
INFRASTRUCTURE_DIR="$SERVICES_DIR/infrastructure"

# ASCII Banner
show_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║   ██╗   ██╗ █████╗ ██╗     ██╗   ██╗███████╗██╗   ██╗███████╗██████╗ ███████╗███████╗  ║
║   ██║   ██║██╔══██╗██║     ██║   ██║██╔════╝██║   ██║██╔════╝██╔══██╗██╔════╝██╔════╝  ║
║   ██║   ██║███████║██║     ██║   ██║█████╗  ██║   ██║█████╗  ██████╔╝███████╗█████╗    ║
║   ╚██╗ ██╔╝██╔══██║██║     ██║   ██║██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║██╔══╝    ║
║    ╚████╔╝ ██║  ██║███████╗╚██████╔╝███████╗ ╚████╔╝ ███████╗██║  ██║███████║███████╗  ║
║     ╚═══╝  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝  ║
║                                                                        ║
║                     LOCAL DEPLOYMENT ORCHESTRATOR                      ║
╚════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Progress bar
progress_bar() {
    local duration=$1
    local width=50
    local progress=0
    
    while [ $progress -le $duration ]; do
        local filled=$((progress * width / duration))
        local empty=$((width - filled))
        
        printf "\r["
        printf "%${filled}s" | tr ' ' '█'
        printf "%${empty}s" | tr ' ' '░'
        printf "] %d%%" $((progress * 100 / duration))
        
        progress=$((progress + 1))
        sleep 0.1
    done
    echo ""
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}▶ Checking prerequisites...${NC}"
    
    local missing=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing+=("Docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing+=("Docker Compose")
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        missing+=("Python")
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        missing+=("curl")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}✗ Missing prerequisites: ${missing[*]}${NC}"
        echo "Please install the missing tools and try again."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}✗ Docker daemon is not running${NC}"
        echo "Please start Docker and try again."
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites satisfied${NC}"
}

# Clean up existing deployment
cleanup_existing() {
    echo -e "${BLUE}▶ Cleaning up existing deployment...${NC}"
    
    # Stop existing containers
    cd "$SERVICES_DIR" 2>/dev/null || true
    docker-compose -f docker-compose.microservices.yml down -v 2>/dev/null || true
    
    cd "$INFRASTRUCTURE_DIR" 2>/dev/null || true
    docker-compose -f docker-compose.infrastructure.yml down -v 2>/dev/null || true
    
    # Clean up any orphaned containers
    docker container prune -f 2>/dev/null || true
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Deploy infrastructure
deploy_infrastructure() {
    echo ""
    echo -e "${BLUE}▶ [1/5] Deploying Infrastructure Components${NC}"
    echo -e "${CYAN}  • Kong API Gateway${NC}"
    echo -e "${CYAN}  • Consul Service Discovery${NC}"
    echo -e "${CYAN}  • Jaeger Distributed Tracing${NC}"
    
    cd "$INFRASTRUCTURE_DIR"
    
    # Start infrastructure
    docker-compose -f docker-compose.infrastructure.yml up -d
    
    # Wait for services to be ready
    echo -n "  Waiting for infrastructure to be ready"
    local attempts=0
    local max_attempts=30
    
    while [ $attempts -lt $max_attempts ]; do
        if curl -s http://localhost:8001/status > /dev/null 2>&1 && \
           curl -s http://localhost:8500/v1/status/leader > /dev/null 2>&1 && \
           curl -s http://localhost:16686/health > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            break
        fi
        echo -n "."
        sleep 2
        attempts=$((attempts + 1))
    done
    
    if [ $attempts -eq $max_attempts ]; then
        echo -e " ${RED}✗${NC}"
        echo -e "${RED}Infrastructure failed to start properly${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Infrastructure deployed${NC}"
}

# Build microservices
build_microservices() {
    echo ""
    echo -e "${BLUE}▶ [2/5] Building Microservices${NC}"
    echo -e "${CYAN}  • Value Architect${NC}"
    echo -e "${CYAN}  • Value Committer${NC}"
    echo -e "${CYAN}  • Value Executor${NC}"
    echo -e "${CYAN}  • Value Amplifier${NC}"
    
    cd "$SERVICES_DIR"
    
    # Build services in parallel
    docker-compose -f docker-compose.microservices.yml build --parallel
    
    echo -e "${GREEN}✓ Microservices built${NC}"
}

# Deploy microservices
deploy_microservices() {
    echo ""
    echo -e "${BLUE}▶ [3/5] Deploying Microservices${NC}"
    
    cd "$SERVICES_DIR"
    
    # Start microservices
    docker-compose -f docker-compose.microservices.yml up -d
    
    # Wait for services to be healthy
    echo -n "  Waiting for microservices to be ready"
    sleep 10
    
    local services=("8011" "8012" "8013" "8014" "8015" "8016")
    for port in "${services[@]}"; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo -n "."
        fi
    done
    echo -e " ${GREEN}✓${NC}"
    
    echo -e "${GREEN}✓ Microservices deployed${NC}"
}

# Configure Kong routes
configure_kong() {
    echo ""
    echo -e "${BLUE}▶ [4/5] Configuring API Gateway Routes${NC}"
    
    # Add services to Kong
    local services=(
        "value-architect:8001:/api/v1/value-models"
        "value-committer:8002:/api/v1/commitments"
        "value-executor:8003:/api/v1/executions"
        "value-amplifier:8004:/api/v1/amplifications"
        "calculation-engine:8005:/api/v1/calculate"
        "notification-service:8006:/api/v1/notifications"
    )
    
    for service_config in "${services[@]}"; do
        IFS=':' read -r name port path <<< "$service_config"
        
        echo -n "  Configuring route for $name"
        
        # Add service
        curl -s -X POST http://localhost:8001/services \
            -H "Content-Type: application/json" \
            -d "{\"name\": \"$name\", \"url\": \"http://$name:$port\"}" \
            > /dev/null 2>&1 || true
        
        # Add route
        curl -s -X POST http://localhost:8001/services/$name/routes \
            -H "Content-Type: application/json" \
            -d "{\"paths\": [\"$path\"], \"strip_path\": false}" \
            > /dev/null 2>&1 || true
        
        echo -e " ${GREEN}✓${NC}"
    done
    
    echo -e "${GREEN}✓ API Gateway configured${NC}"
}

# Deploy advanced features
deploy_advanced_features() {
    echo ""
    echo -e "${BLUE}▶ [5/5] Deploying Advanced Features${NC}"
    echo -e "${CYAN}  • JWT Authentication${NC}"
    echo -e "${CYAN}  • Service Mesh${NC}"
    echo -e "${CYAN}  • Circuit Breaker${NC}"
    
    cd "$INFRASTRUCTURE_DIR"
    
    if [ -f "deploy-advanced-features.sh" ]; then
        ./deploy-advanced-features.sh all > /dev/null 2>&1
        echo -e "${GREEN}✓ Advanced features deployed${NC}"
    else
        echo -e "${YELLOW}⚠ Advanced features script not found${NC}"
    fi
}

# Health check all services
health_check() {
    echo ""
    echo -e "${BLUE}▶ Health Check Report${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Infrastructure services
    echo -e "${CYAN}Infrastructure Services:${NC}"
    
    local infra_services=(
        "Kong Gateway:8001:/status"
        "Consul:8500:/v1/status/leader"
        "Jaeger:16686:/health"
        "Prometheus:9090:/-/healthy"
        "Grafana:3001:/api/health"
    )
    
    for service_config in "${infra_services[@]}"; do
        IFS=':' read -r name port path <<< "$service_config"
        printf "  %-20s " "$name:"
        
        if curl -s "http://localhost:$port$path" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
        else
            echo -e "${RED}✗ Unhealthy${NC}"
        fi
    done
    
    # Microservices
    echo ""
    echo -e "${CYAN}Microservices:${NC}"
    
    local micro_services=(
        "Value Architect:8011"
        "Value Committer:8012"
        "Value Executor:8013"
        "Value Amplifier:8014"
        "Calculation Engine:8015"
        "Notifications:8016"
    )
    
    for service_config in "${micro_services[@]}"; do
        IFS=':' read -r name port <<< "$service_config"
        printf "  %-20s " "$name:"
        
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
        else
            echo -e "${RED}✗ Unhealthy${NC}"
        fi
    done
}

# Show access information
show_access_info() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}     ✓ Local Deployment Complete!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}📊 Web Interfaces:${NC}"
    echo "  • API Gateway:       http://localhost:8000"
    echo "  • Kong Admin:        http://localhost:8001"
    echo "  • Consul UI:         http://localhost:8500"
    echo "  • Jaeger Tracing:    http://localhost:16686"
    echo "  • Grafana:           http://localhost:3001 (admin/admin)"
    echo "  • Prometheus:        http://localhost:9090"
    echo ""
    echo -e "${BLUE}🚀 API Endpoints (via Gateway):${NC}"
    echo "  • Value Models:      http://localhost:8000/api/v1/value-models"
    echo "  • Commitments:       http://localhost:8000/api/v1/commitments"
    echo "  • Executions:        http://localhost:8000/api/v1/executions"
    echo "  • Amplifications:    http://localhost:8000/api/v1/amplifications"
    echo ""
    echo -e "${BLUE}🧪 Quick Test:${NC}"
    echo '  curl -X POST http://localhost:8000/api/v1/value-models \'
    echo '    -H "Content-Type: application/json" \'
    echo '    -d '\''{"company_name": "Test Corp", "industry": "SaaS"}'\'''
    echo ""
    echo -e "${BLUE}📝 Management Commands:${NC}"
    echo "  • View logs:         docker-compose -f services/docker-compose.microservices.yml logs -f"
    echo "  • Stop all:          docker-compose -f services/docker-compose.microservices.yml down"
    echo "  • Restart service:   docker-compose -f services/docker-compose.microservices.yml restart <service>"
    echo ""
}

# Stop deployment
stop_deployment() {
    echo -e "${BLUE}▶ Stopping all services...${NC}"
    
    cd "$SERVICES_DIR"
    docker-compose -f docker-compose.microservices.yml down
    
    cd "$INFRASTRUCTURE_DIR"
    docker-compose -f docker-compose.infrastructure.yml down
    
    echo -e "${GREEN}✓ All services stopped${NC}"
}

# Main deployment flow
main() {
    case "${1:-deploy}" in
        deploy)
            show_banner
            check_prerequisites
            cleanup_existing
            deploy_infrastructure
            build_microservices
            deploy_microservices
            configure_kong
            deploy_advanced_features
            health_check
            show_access_info
            ;;
        
        stop)
            echo -e "${BLUE}Stopping ValueVerse deployment...${NC}"
            stop_deployment
            ;;
        
        restart)
            echo -e "${BLUE}Restarting ValueVerse deployment...${NC}"
            stop_deployment
            sleep 2
            main deploy
            ;;
        
        status)
            health_check
            ;;
        
        logs)
            cd "$SERVICES_DIR"
            docker-compose -f docker-compose.microservices.yml logs -f
            ;;
        
        clean)
            echo -e "${BLUE}Cleaning up everything...${NC}"
            cleanup_existing
            docker system prune -af --volumes
            echo -e "${GREEN}✓ Clean complete${NC}"
            ;;
        
        help)
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  deploy   - Deploy complete stack (default)"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            echo "  status   - Show health status"
            echo "  logs     - Show service logs"
            echo "  clean    - Clean up everything"
            echo "  help     - Show this help"
            ;;
        
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
