#!/bin/bash

# Deploy and manage microservices
set -e

COMMAND=${1:-help}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker and Docker Compose
check_prerequisites() {
    echo_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        echo_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo_error "Docker Compose is not installed"
        exit 1
    fi
    
    echo_info "Prerequisites OK ✅"
}

# Build all microservices
build_services() {
    echo_info "Building microservices..."
    docker-compose -f docker-compose.microservices.yml build --parallel
    echo_info "Build complete ✅"
}

# Start all services
start_services() {
    echo_info "Starting microservices..."
    docker-compose -f docker-compose.microservices.yml up -d
    echo_info "Services started ✅"
    
    echo ""
    echo_info "Waiting for services to be healthy..."
    sleep 10
    
    check_health
}

# Stop all services
stop_services() {
    echo_info "Stopping microservices..."
    docker-compose -f docker-compose.microservices.yml down
    echo_info "Services stopped ✅"
}

# Check health of all services
check_health() {
    echo_info "Checking service health..."
    
    services=("value-architect:8011" "value-committer:8012" "value-executor:8013" "value-amplifier:8014" "calculation-engine:8015" "notification-service:8016")
    
    for service in "${services[@]}"; do
        name="${service%%:*}"
        port="${service##*:}"
        
        if curl -f "http://localhost:$port/health" &> /dev/null; then
            echo_info "✅ $name is healthy"
        else
            echo_warn "⚠️ $name is not responding"
        fi
    done
}

# View logs
view_logs() {
    service=${2:-}
    if [ -z "$service" ]; then
        docker-compose -f docker-compose.microservices.yml logs -f
    else
        docker-compose -f docker-compose.microservices.yml logs -f $service
    fi
}

# Test the microservices
test_services() {
    echo_info "Testing microservices..."
    
    # Test Value Architect
    echo_info "Testing Value Architect..."
    curl -X POST "http://localhost:8011/api/v1/value-models" \
        -H "Content-Type: application/json" \
        -d '{
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "company_size": "mid-market",
            "target_metrics": ["revenue_growth", "cost_reduction"]
        }' | python -m json.tool
    
    echo ""
    echo_info "Test complete ✅"
}

# Scale a service
scale_service() {
    service=$2
    replicas=$3
    
    if [ -z "$service" ] || [ -z "$replicas" ]; then
        echo_error "Usage: ./deploy-microservices.sh scale <service> <replicas>"
        exit 1
    fi
    
    echo_info "Scaling $service to $replicas replicas..."
    docker-compose -f docker-compose.microservices.yml up -d --scale $service=$replicas
    echo_info "Scaling complete ✅"
}

# Show service URLs
show_urls() {
    echo ""
    echo_info "🌐 Service URLs:"
    echo ""
    echo "  Core Services:"
    echo "    - API Gateway:         http://localhost:8000"
    echo "    - Value Architect:     http://localhost:8011"
    echo "    - Value Committer:     http://localhost:8012"
    echo "    - Value Executor:      http://localhost:8013"
    echo "    - Value Amplifier:     http://localhost:8014"
    echo "    - Calculation Engine:  http://localhost:8015"
    echo "    - Notifications:       http://localhost:8016"
    echo ""
    echo "  Infrastructure:"
    echo "    - PostgreSQL:          localhost:5432"
    echo "    - Redis:               localhost:6379"
    echo "    - RabbitMQ:            http://localhost:15672 (admin/admin)"
    echo ""
    echo "  Monitoring:"
    echo "    - Grafana:             http://localhost:3001 (admin/admin)"
    echo "    - Prometheus:          http://localhost:9090"
    echo "    - Jaeger:              http://localhost:16686"
    echo "    - Consul:              http://localhost:8500"
    echo ""
}

# Main command handler
case "$COMMAND" in
    build)
        check_prerequisites
        build_services
        ;;
    start)
        check_prerequisites
        start_services
        show_urls
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services
        show_urls
        ;;
    health)
        check_health
        ;;
    logs)
        view_logs $@
        ;;
    test)
        test_services
        ;;
    scale)
        scale_service $@
        ;;
    urls)
        show_urls
        ;;
    help)
        echo "ValueVerse Microservices Deployment Tool"
        echo ""
        echo "Usage: ./deploy-microservices.sh [command]"
        echo ""
        echo "Commands:"
        echo "  build     - Build all microservice Docker images"
        echo "  start     - Start all microservices"
        echo "  stop      - Stop all microservices"
        echo "  restart   - Restart all microservices"
        echo "  health    - Check health of all services"
        echo "  logs      - View logs (optional: service name)"
        echo "  test      - Run basic tests"
        echo "  scale     - Scale a service (e.g., scale value-architect 3)"
        echo "  urls      - Show all service URLs"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./deploy-microservices.sh start"
        echo "  ./deploy-microservices.sh logs value-architect"
        echo "  ./deploy-microservices.sh scale calculation-engine 5"
        ;;
    *)
        echo_error "Unknown command: $COMMAND"
        echo "Run './deploy-microservices.sh help' for usage"
        exit 1
        ;;
esac
