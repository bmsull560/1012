#!/bin/bash

# ============================================================================
# ValueVerse Platform - One-Command Deployment Script
# ============================================================================
# This script deploys the entire ValueVerse platform with a single command
# Usage: ./deploy.sh [environment] [options]
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="ValueVerse"
COMPOSE_FILE="docker-compose.complete.yml"
ENV_FILE=".env"
LOG_FILE="deployment.log"
REQUIRED_PORTS=(3000 3001 5432 5672 6379 8000 8001 8011 8012 8013 8014 8015 8016 8500 9090 15672 16686)

# Timing
START_TIME=$(date +%s)

# ============================================================================
# Functions
# ============================================================================

# Show banner
show_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║   ██╗   ██╗ █████╗ ██╗     ██╗   ██╗███████╗██╗   ██╗███████╗██████╗ ███████╗███████╗  ║
║   ██║   ██║██╔══██╗██║     ██║   ██║██╔════╝██║   ██║██╔════╝██╔══██╗██╔════╝██╔════╝  ║
║   ██║   ██║███████║██║     ██║   ██║█████╗  ██║   ██║█████╗  ██████╔╝███████╗█████╗    ║
║   ╚██╗ ██╔╝██╔══██║██║     ██║   ██║██╔══╝  ╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║██╔══╝    ║
║    ╚████╔╝ ██║  ██║███████╗╚██████╔╝███████╗ ╚████╔╝ ███████╗██║  ██║███████║███████╗  ║
║     ╚═══╝  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝  ║
║                                                                            ║
║                    🚀 ONE-COMMAND DEPLOYMENT SYSTEM 🚀                    ║
╚════════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Log function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
        SUCCESS)
            echo -e "${GREEN}✓${NC} $message"
            ;;
        WARNING)
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
        ERROR)
            echo -e "${RED}✗${NC} $message"
            ;;
        *)
            echo "$message"
            ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Progress spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Version comparison
version_ge() {
    [ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

# Check prerequisites
check_prerequisites() {
    log INFO "Checking prerequisites..."
    
    local errors=0
    
    # Check Docker
    if command_exists docker; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        if version_ge "$docker_version" "20.10.0"; then
            log SUCCESS "Docker $docker_version found"
        else
            log ERROR "Docker version $docker_version is too old. Required: 20.10.0+"
            errors=$((errors + 1))
        fi
    else
        log ERROR "Docker is not installed"
        errors=$((errors + 1))
    fi
    
    # Check Docker Compose
    if command_exists docker && docker compose version >/dev/null 2>&1; then
        local compose_version=$(docker compose version | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | sed 's/v//')
        if version_ge "$compose_version" "2.0.0"; then
            log SUCCESS "Docker Compose $compose_version found"
        else
            log ERROR "Docker Compose version $compose_version is too old. Required: 2.0.0+"
            errors=$((errors + 1))
        fi
    else
        log ERROR "Docker Compose is not installed"
        errors=$((errors + 1))
    fi
    
    # Check Git
    if command_exists git; then
        log SUCCESS "Git found"
    else
        log WARNING "Git is not installed (optional)"
    fi
    
    # Check available memory
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        local available_mem=$(free -m | awk 'NR==2{print $7}')
        if [ "$available_mem" -lt 4000 ]; then
            log WARNING "Available memory is low: ${available_mem}MB (recommended: 8000MB+)"
        else
            log SUCCESS "Available memory: ${available_mem}MB"
        fi
    fi
    
    # Check disk space
    local available_space=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$available_space" -lt 10 ]; then
        log WARNING "Available disk space is low: ${available_space}GB (recommended: 20GB+)"
    else
        log SUCCESS "Available disk space: ${available_space}GB"
    fi
    
    if [ $errors -gt 0 ]; then
        log ERROR "Prerequisites check failed. Please install missing dependencies."
        exit 1
    fi
    
    log SUCCESS "All prerequisites satisfied"
}

# Check ports
check_ports() {
    log INFO "Checking port availability..."
    
    local ports_in_use=()
    
    for port in "${REQUIRED_PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            ports_in_use+=($port)
        fi
    done
    
    if [ ${#ports_in_use[@]} -gt 0 ]; then
        log ERROR "The following ports are already in use: ${ports_in_use[*]}"
        log INFO "Please stop conflicting services or change port configuration"
        
        read -p "Do you want to stop conflicting containers? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_conflicting_containers
        else
            exit 1
        fi
    else
        log SUCCESS "All required ports are available"
    fi
}

# Stop conflicting containers
stop_conflicting_containers() {
    log INFO "Stopping conflicting containers..."
    
    # Find and stop containers using our ports
    for port in "${REQUIRED_PORTS[@]}"; do
        local container=$(docker ps --format "table {{.Names}}" | grep -E "valueverse|frontend|services|infrastructure" | head -1)
        if [ ! -z "$container" ]; then
            docker stop $container >/dev/null 2>&1 || true
        fi
    done
    
    log SUCCESS "Conflicting containers stopped"
}

# Setup environment
setup_environment() {
    log INFO "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        log INFO "Creating .env file from template..."
        cat > "$ENV_FILE" << EOL
# ValueVerse Platform Environment Configuration
# Generated: $(date)

# Environment
NODE_ENV=development
LOG_LEVEL=info

# Database
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=valueverse

# Redis
REDIS_PASSWORD=

# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASS=admin

# API Gateway
API_URL=http://localhost:8000
WS_URL=ws://localhost:8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# JWT Secret (generate a secure one for production!)
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Stripe (optional)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# SMTP (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
EOL
        log SUCCESS ".env file created"
    else
        log INFO ".env file already exists"
    fi
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p data
    mkdir -p scripts
    
    log SUCCESS "Environment setup complete"
}

# Build services
build_services() {
    log INFO "Building Docker images..."
    
    (docker compose -f "$COMPOSE_FILE" build --parallel 2>&1 | tee -a "$LOG_FILE" > /dev/null) &
    spinner $!
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log SUCCESS "All images built successfully"
    else
        log ERROR "Failed to build images. Check $LOG_FILE for details"
        exit 1
    fi
}

# Start services
start_services() {
    log INFO "Starting services..."
    
    # Start infrastructure first
    log INFO "Starting infrastructure services..."
    docker compose -f "$COMPOSE_FILE" up -d postgres redis rabbitmq 2>&1 | tee -a "$LOG_FILE" > /dev/null
    sleep 5
    
    # Start Kong and infrastructure
    log INFO "Starting API Gateway and monitoring..."
    docker compose -f "$COMPOSE_FILE" up -d kong-database kong-migration 2>&1 | tee -a "$LOG_FILE" > /dev/null
    sleep 10
    docker compose -f "$COMPOSE_FILE" up -d kong consul jaeger prometheus grafana 2>&1 | tee -a "$LOG_FILE" > /dev/null
    sleep 5
    
    # Start microservices
    log INFO "Starting microservices..."
    docker compose -f "$COMPOSE_FILE" up -d value-architect value-committer value-executor value-amplifier calculation-engine notification-service 2>&1 | tee -a "$LOG_FILE" > /dev/null
    sleep 5
    
    # Start frontend
    log INFO "Starting frontend..."
    docker compose -f "$COMPOSE_FILE" up -d frontend 2>&1 | tee -a "$LOG_FILE" > /dev/null
    
    log SUCCESS "All services started"
}

# Configure Kong routes
configure_kong() {
    log INFO "Configuring API Gateway routes..."
    
    sleep 10  # Wait for Kong to be ready
    
    # Configure services in Kong
    local services=(
        "value-architect:http://value-architect:8001:/api/v1/value-models"
        "value-committer:http://value-committer:8002:/api/v1/commitments"
        "value-executor:http://value-executor:8003:/api/v1/executions"
        "value-amplifier:http://value-amplifier:8004:/api/v1/amplifications"
        "calculation-engine:http://calculation-engine:8005:/api/v1/calculate"
        "notification-service:http://notification-service:8006:/api/v1/notifications"
    )
    
    for service_config in "${services[@]}"; do
        IFS=':' read -r name url path <<< "$service_config"
        
        # Add service
        curl -s -X POST http://localhost:8001/services \
            -H "Content-Type: application/json" \
            -d "{\"name\": \"$name\", \"url\": \"$url\"}" \
            > /dev/null 2>&1 || true
        
        # Add route
        curl -s -X POST http://localhost:8001/services/$name/routes \
            -H "Content-Type: application/json" \
            -d "{\"paths\": [\"$path\"], \"strip_path\": false}" \
            > /dev/null 2>&1 || true
    done
    
    log SUCCESS "API Gateway configured"
}

# Run database migrations
run_migrations() {
    log INFO "Running database migrations..."
    
    # Wait for database to be ready
    sleep 5
    
    # Run migrations (if migration scripts exist)
    if [ -f "scripts/migrate.sql" ]; then
        docker exec -i valueverse-postgres psql -U postgres -d valueverse < scripts/migrate.sql 2>&1 | tee -a "$LOG_FILE" > /dev/null
        log SUCCESS "Database migrations completed"
    else
        log INFO "No migrations to run"
    fi
}

# Seed sample data
seed_data() {
    log INFO "Seeding sample data..."
    
    # Create sample data script if it doesn't exist
    if [ ! -f "scripts/seed-data.sql" ]; then
        cat > "scripts/seed-data.sql" << 'EOL'
-- Sample data for ValueVerse platform
INSERT INTO users (email, name, role) VALUES 
    ('admin@valueverse.ai', 'Admin User', 'admin'),
    ('demo@valueverse.ai', 'Demo User', 'user')
ON CONFLICT DO NOTHING;

INSERT INTO companies (name, industry, size) VALUES 
    ('Acme Corp', 'SaaS', 'mid-market'),
    ('TechStart Inc', 'FinTech', 'startup'),
    ('Enterprise Co', 'Healthcare', 'enterprise')
ON CONFLICT DO NOTHING;
EOL
    fi
    
    # Run seed script
    docker exec -i valueverse-postgres psql -U postgres -d valueverse < scripts/seed-data.sql 2>&1 | tee -a "$LOG_FILE" > /dev/null || true
    
    log SUCCESS "Sample data loaded"
}

# Health check
health_check() {
    log INFO "Running health checks..."
    
    local unhealthy=()
    
    # Check each service
    local services=(
        "PostgreSQL:5432"
        "Redis:6379"
        "RabbitMQ:15672"
        "Kong:8001"
        "Consul:8500"
        "Jaeger:16686"
        "Prometheus:9090"
        "Grafana:3001"
        "Value-Architect:8011"
        "Value-Committer:8012"
        "Value-Executor:8013"
        "Value-Amplifier:8014"
        "Frontend:3000"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -s -f http://localhost:$port/health >/dev/null 2>&1 || curl -s -f http://localhost:$port >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $name"
        else
            echo -e "  ${RED}✗${NC} $name"
            unhealthy+=($name)
        fi
    done
    
    if [ ${#unhealthy[@]} -gt 0 ]; then
        log WARNING "Some services are not healthy: ${unhealthy[*]}"
    else
        log SUCCESS "All services are healthy"
    fi
}

# Show success message
show_success() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           🎉 DEPLOYMENT SUCCESSFUL! 🎉${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}📊 Access Points:${NC}"
    echo -e "  ${BLUE}Main Application:${NC}     http://localhost:3000"
    echo -e "  ${BLUE}API Gateway:${NC}          http://localhost:8000"
    echo -e "  ${BLUE}Grafana Dashboard:${NC}    http://localhost:3001 (admin/admin)"
    echo -e "  ${BLUE}Consul UI:${NC}            http://localhost:8500"
    echo -e "  ${BLUE}Jaeger Tracing:${NC}       http://localhost:16686"
    echo -e "  ${BLUE}RabbitMQ Management:${NC}  http://localhost:15672 (admin/admin)"
    echo ""
    echo -e "${CYAN}🔑 Default Credentials:${NC}"
    echo -e "  ${BLUE}Application:${NC} admin@valueverse.ai / admin123"
    echo -e "  ${BLUE}Grafana:${NC}     admin / admin"
    echo -e "  ${BLUE}RabbitMQ:${NC}    admin / admin"
    echo ""
    echo -e "${CYAN}📝 Useful Commands:${NC}"
    echo -e "  ${BLUE}View logs:${NC}        docker compose -f $COMPOSE_FILE logs -f"
    echo -e "  ${BLUE}Stop all:${NC}         docker compose -f $COMPOSE_FILE down"
    echo -e "  ${BLUE}Restart service:${NC}  docker compose -f $COMPOSE_FILE restart <service>"
    echo -e "  ${BLUE}Health check:${NC}     ./deploy.sh health"
    echo ""
    echo -e "${GREEN}Deployment completed in ${duration} seconds${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
}

# Cleanup function
cleanup() {
    log INFO "Cleaning up..."
    docker compose -f "$COMPOSE_FILE" down -v
    rm -f "$LOG_FILE"
    log SUCCESS "Cleanup complete"
}

# Stop function
stop_all() {
    log INFO "Stopping all services..."
    docker compose -f "$COMPOSE_FILE" down
    log SUCCESS "All services stopped"
}

# Main function
main() {
    local command=${1:-deploy}
    
    case $command in
        deploy)
            show_banner
            check_prerequisites
            check_ports
            setup_environment
            build_services
            start_services
            configure_kong
            run_migrations
            seed_data
            health_check
            show_success
            ;;
        
        start)
            log INFO "Starting services..."
            start_services
            configure_kong
            health_check
            ;;
        
        stop)
            stop_all
            ;;
        
        restart)
            stop_all
            sleep 2
            start_services
            configure_kong
            health_check
            ;;
        
        health)
            health_check
            ;;
        
        logs)
            docker compose -f "$COMPOSE_FILE" logs -f ${2:-}
            ;;
        
        clean)
            cleanup
            ;;
        
        build)
            build_services
            ;;
        
        help)
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  deploy    - Full deployment (default)"
            echo "  start     - Start all services"
            echo "  stop      - Stop all services"
            echo "  restart   - Restart all services"
            echo "  health    - Check service health"
            echo "  logs      - View logs (optional: service name)"
            echo "  clean     - Remove all containers and volumes"
            echo "  build     - Build all images"
            echo "  help      - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                    # Deploy everything"
            echo "  $0 logs frontend      # View frontend logs"
            echo "  $0 restart           # Restart all services"
            ;;
        
        *)
            log ERROR "Unknown command: $command"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Trap errors
trap 'log ERROR "Deployment failed. Check $LOG_FILE for details"; exit 1' ERR

# Run main function
main "$@"
