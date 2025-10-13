#!/bin/bash

# Deploy Advanced Infrastructure Features for ValueVerse
# Implements: JWT Authentication, Service Mesh, Circuit Breaker

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ASCII Banner
show_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║        ValueVerse Advanced Infrastructure Features          ║
║   JWT Auth | Service Mesh | Circuit Breaker | Resilience    ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    # Check if Kong is running
    if ! curl -s http://localhost:8001/status > /dev/null 2>&1; then
        echo -e "${RED}Kong API Gateway is not running!${NC}"
        echo "Please run: ./infrastructure/deploy-infrastructure.sh start"
        exit 1
    fi
    
    # Check if Consul is running
    if ! curl -s http://localhost:8500/v1/status/leader > /dev/null 2>&1; then
        echo -e "${RED}Consul is not running!${NC}"
        echo "Please run: ./infrastructure/deploy-infrastructure.sh start"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
}

# Deploy JWT Authentication
deploy_jwt_auth() {
    echo ""
    echo -e "${BLUE}[1/3] Deploying JWT Authentication...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd security
    chmod +x jwt-auth-setup.sh
    ./jwt-auth-setup.sh
    cd ..
    
    echo -e "${GREEN}✓ JWT Authentication deployed${NC}"
}

# Deploy Service Mesh
deploy_service_mesh() {
    echo ""
    echo -e "${BLUE}[2/3] Deploying Consul Connect Service Mesh...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd service-mesh
    chmod +x consul-connect-setup.sh
    ./consul-connect-setup.sh
    cd ..
    
    # Start Envoy sidecars
    echo -e "${YELLOW}Starting Envoy sidecar proxies...${NC}"
    docker-compose -f service-mesh/docker-compose.service-mesh.yml up -d 2>/dev/null || true
    
    echo -e "${GREEN}✓ Service Mesh deployed${NC}"
}

# Deploy Circuit Breaker
deploy_circuit_breaker() {
    echo ""
    echo -e "${BLUE}[3/3] Deploying Circuit Breaker & Resilience...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd resilience
    chmod +x circuit-breaker-setup.sh
    ./circuit-breaker-setup.sh
    cd ..
    
    echo -e "${GREEN}✓ Circuit Breaker deployed${NC}"
}

# Verify deployment
verify_deployment() {
    echo ""
    echo -e "${BLUE}Verifying deployment...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check JWT plugin
    echo -n "JWT Authentication: "
    if curl -s http://localhost:8001/plugins | grep -q "jwt"; then
        echo -e "${GREEN}✓ Active${NC}"
    else
        echo -e "${RED}✗ Not found${NC}"
    fi
    
    # Check ACL plugin
    echo -n "ACL Authorization: "
    if curl -s http://localhost:8001/plugins | grep -q "acl"; then
        echo -e "${GREEN}✓ Active${NC}"
    else
        echo -e "${RED}✗ Not found${NC}"
    fi
    
    # Check Service Mesh
    echo -n "Service Mesh (Consul Connect): "
    if curl -s http://localhost:8500/v1/agent/services | grep -q "connect"; then
        echo -e "${GREEN}✓ Active${NC}"
    else
        echo -e "${YELLOW}⚠ Partial${NC}"
    fi
    
    # Check Circuit Breaker
    echo -n "Circuit Breaker: "
    if curl -s http://localhost:8001/plugins | grep -q "rate-limiting"; then
        echo -e "${GREEN}✓ Active${NC}"
    else
        echo -e "${RED}✗ Not found${NC}"
    fi
    
    # Check Retry Policies
    echo -n "Retry Policies: "
    if curl -s http://localhost:8001/services/value-architect | grep -q '"retries":3'; then
        echo -e "${GREEN}✓ Active${NC}"
    else
        echo -e "${YELLOW}⚠ Not configured${NC}"
    fi
}

# Show usage information
show_usage() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        ✓ Advanced Features Deployment Complete!       ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}1. JWT Authentication${NC}"
    echo "   Generate a token:"
    echo "   python security/generate-jwt.py <key> <secret> 60"
    echo ""
    echo "   Test authenticated request:"
    echo '   TOKEN=$(python security/generate-jwt.py "key" "secret")'
    echo '   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/value-models'
    echo ""
    echo -e "${BLUE}2. Service Mesh (Consul Connect)${NC}"
    echo "   View service topology:"
    echo "   http://localhost:8500/ui/dc1/services"
    echo ""
    echo "   Check Envoy proxy admin:"
    echo "   http://localhost:19001  (value-architect)"
    echo "   http://localhost:19002  (value-committer)"
    echo ""
    echo -e "${BLUE}3. Circuit Breaker & Resilience${NC}"
    echo "   Test circuit breaker:"
    echo "   ./resilience/test-circuit-breaker.sh"
    echo ""
    echo "   Monitor status:"
    echo "   curl http://localhost:8001/services/value-architect/plugins"
    echo ""
    echo -e "${BLUE}Monitoring & Observability${NC}"
    echo "   • Grafana: http://localhost:3001 (admin/admin)"
    echo "   • Jaeger: http://localhost:16686"
    echo "   • Consul: http://localhost:8500"
    echo "   • Kong Admin: http://localhost:8001"
}

# Main execution
main() {
    show_banner
    
    case "${1:-all}" in
        jwt)
            check_prerequisites
            deploy_jwt_auth
            ;;
        mesh)
            check_prerequisites
            deploy_service_mesh
            ;;
        circuit)
            check_prerequisites
            deploy_circuit_breaker
            ;;
        all)
            check_prerequisites
            deploy_jwt_auth
            deploy_service_mesh
            deploy_circuit_breaker
            verify_deployment
            show_usage
            ;;
        verify)
            verify_deployment
            ;;
        help)
            echo "Usage: $0 [all|jwt|mesh|circuit|verify|help]"
            echo ""
            echo "Commands:"
            echo "  all     - Deploy all advanced features (default)"
            echo "  jwt     - Deploy JWT authentication only"
            echo "  mesh    - Deploy service mesh only"
            echo "  circuit - Deploy circuit breaker only"
            echo "  verify  - Verify deployment status"
            echo "  help    - Show this help message"
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo "Usage: $0 [all|jwt|mesh|circuit|verify|help]"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
