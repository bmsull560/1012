#!/bin/bash

# Deploy Infrastructure Components for ValueVerse Microservices
# Includes: Kong API Gateway, Consul Service Discovery, Jaeger Distributed Tracing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
echo_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

COMMAND=${1:-help}

# ASCII Banner
show_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
╔══════════════════════════════════════════════════════╗
║     ValueVerse Infrastructure Components Setup      ║
║  Kong Gateway | Consul Discovery | Jaeger Tracing   ║
╚══════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo_info "Checking prerequisites..."
    
    local missing=0
    
    if ! command -v docker &> /dev/null; then
        echo_error "Docker is not installed"
        missing=1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo_error "Docker Compose is not installed"
        missing=1
    fi
    
    if ! command -v curl &> /dev/null; then
        echo_warning "curl is not installed (needed for testing)"
    fi
    
    if [ $missing -eq 1 ]; then
        exit 1
    fi
    
    echo_success "Prerequisites satisfied"
}

# Start infrastructure services
start_infrastructure() {
    echo_info "Starting infrastructure services..."
    
    # Start the infrastructure stack
    docker-compose -f docker-compose.infrastructure.yml up -d
    
    echo_info "Waiting for services to be ready..."
    
    # Wait for Kong
    echo -n "Waiting for Kong API Gateway..."
    until curl -s http://localhost:8001/status > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " Ready!"
    
    # Wait for Consul
    echo -n "Waiting for Consul..."
    until curl -s http://localhost:8500/v1/status/leader > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " Ready!"
    
    # Wait for Jaeger
    echo -n "Waiting for Jaeger..."
    until curl -s http://localhost:16686/health > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " Ready!"
    
    echo_success "All infrastructure services are running!"
}

# Configure Kong API Gateway
configure_kong() {
    echo_info "Configuring Kong API Gateway..."
    
    # Wait for Kong to be ready
    sleep 5
    
    # Add services to Kong
    echo_info "Adding Value Architect service to Kong..."
    curl -X POST http://localhost:8001/services \
        -H "Content-Type: application/json" \
        -d '{
            "name": "value-architect",
            "url": "http://value-architect:8001"
        }' 2>/dev/null || true
    
    # Add routes
    curl -X POST http://localhost:8001/services/value-architect/routes \
        -H "Content-Type: application/json" \
        -d '{
            "paths": ["/api/v1/value-models"],
            "strip_path": false
        }' 2>/dev/null || true
    
    # Enable plugins
    echo_info "Enabling Kong plugins..."
    
    # Rate limiting
    curl -X POST http://localhost:8001/plugins \
        -H "Content-Type: application/json" \
        -d '{
            "name": "rate-limiting",
            "config": {
                "minute": 100,
                "hour": 10000
            }
        }' 2>/dev/null || true
    
    # CORS
    curl -X POST http://localhost:8001/plugins \
        -H "Content-Type: application/json" \
        -d '{
            "name": "cors",
            "config": {
                "origins": ["*"],
                "credentials": true
            }
        }' 2>/dev/null || true
    
    # Zipkin tracing
    curl -X POST http://localhost:8001/plugins \
        -H "Content-Type: application/json" \
        -d '{
            "name": "zipkin",
            "config": {
                "http_endpoint": "http://jaeger:9411/api/v2/spans",
                "sample_ratio": 1.0
            }
        }' 2>/dev/null || true
    
    echo_success "Kong configured successfully"
}

# Register services with Consul
register_consul_services() {
    echo_info "Registering services with Consul..."
    
    # Register Value Architect
    curl -X PUT http://localhost:8500/v1/agent/service/register \
        -H "Content-Type: application/json" \
        -d '{
            "ID": "value-architect-1",
            "Name": "value-architect",
            "Tags": ["primary", "v1"],
            "Address": "value-architect",
            "Port": 8001,
            "Check": {
                "HTTP": "http://value-architect:8001/health",
                "Interval": "10s"
            }
        }' 2>/dev/null || true
    
    echo_success "Services registered with Consul"
}

# Test the infrastructure
test_infrastructure() {
    echo_info "Testing infrastructure components..."
    
    # Test Kong
    echo -n "Testing Kong Gateway... "
    if curl -s http://localhost:8001/status | grep -q "database"; then
        echo_success "OK"
    else
        echo_error "FAILED"
    fi
    
    # Test Consul
    echo -n "Testing Consul... "
    if curl -s http://localhost:8500/v1/status/leader | grep -q "8300"; then
        echo_success "OK"
    else
        echo_error "FAILED"
    fi
    
    # Test Jaeger
    echo -n "Testing Jaeger... "
    if curl -s http://localhost:16686/health | grep -q "Server available"; then
        echo_success "OK"
    else
        echo_error "FAILED"
    fi
    
    # Test service discovery
    echo_info "Testing service discovery..."
    curl -s http://localhost:8500/v1/catalog/services | python -m json.tool
    
    echo_success "Infrastructure tests complete"
}

# Stop infrastructure
stop_infrastructure() {
    echo_info "Stopping infrastructure services..."
    docker-compose -f docker-compose.infrastructure.yml down
    echo_success "Infrastructure services stopped"
}

# View logs
view_logs() {
    service=${2:-}
    if [ -z "$service" ]; then
        docker-compose -f docker-compose.infrastructure.yml logs -f
    else
        docker-compose -f docker-compose.infrastructure.yml logs -f $service
    fi
}

# Show URLs
show_urls() {
    echo ""
    echo_info "Infrastructure Service URLs:"
    echo ""
    echo "  ${GREEN}Kong API Gateway${NC}"
    echo "    Proxy:        http://localhost:8000"
    echo "    Admin API:    http://localhost:8001"
    echo "    Admin UI:     http://localhost:1337 (Konga)"
    echo ""
    echo "  ${GREEN}Consul Service Discovery${NC}"
    echo "    UI:           http://localhost:8500"
    echo "    DNS:          localhost:8600"
    echo "    API:          http://localhost:8500/v1/"
    echo ""
    echo "  ${GREEN}Jaeger Distributed Tracing${NC}"
    echo "    UI:           http://localhost:16686"
    echo "    Collector:    http://localhost:14268"
    echo "    Zipkin:       http://localhost:9411"
    echo "    Metrics:      http://localhost:14269/metrics"
    echo ""
    echo "  ${GREEN}Additional Services${NC}"
    echo "    Zipkin UI:    http://localhost:9412"
    echo "    OTEL:         http://localhost:4318"
    echo ""
}

# Main command handler
case "$COMMAND" in
    start)
        show_banner
        check_prerequisites
        start_infrastructure
        sleep 10
        configure_kong
        register_consul_services
        show_urls
        echo ""
        echo_success "Infrastructure deployment complete!"
        ;;
    
    stop)
        stop_infrastructure
        ;;
    
    restart)
        stop_infrastructure
        sleep 2
        start_infrastructure
        configure_kong
        register_consul_services
        show_urls
        ;;
    
    test)
        test_infrastructure
        ;;
    
    logs)
        view_logs $@
        ;;
    
    urls)
        show_urls
        ;;
    
    configure)
        configure_kong
        register_consul_services
        ;;
    
    help|*)
        show_banner
        echo "Usage: ./deploy-infrastructure.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start      - Start all infrastructure services"
        echo "  stop       - Stop all infrastructure services"
        echo "  restart    - Restart all services"
        echo "  test       - Test infrastructure components"
        echo "  logs       - View logs (optional: service name)"
        echo "  urls       - Show all service URLs"
        echo "  configure  - Configure Kong and Consul"
        echo "  help       - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./deploy-infrastructure.sh start"
        echo "  ./deploy-infrastructure.sh logs kong"
        echo "  ./deploy-infrastructure.sh test"
        ;;
esac
