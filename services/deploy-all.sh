#!/bin/bash

# Complete deployment script for ValueVerse Microservices with Infrastructure
# Deploys: Kong, Consul, Jaeger, and all microservices

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
 ██▒   █▓ ▄▄▄       ██▓     █    ██ ▓█████  ██▒   █▓▓█████  ██▀███    ██████ ▓█████ 
▓██░   █▒▒████▄    ▓██▒     ██  ▓██▒▓█   ▀ ▓██░   █▒▓█   ▀ ▓██ ▒ ██▒▒██    ▒ ▓█   ▀ 
 ▓██  █▒░▒██  ▀█▄  ▒██░    ▓██  ▒██░▒███    ▓██  █▒░▒███   ▓██ ░▄█ ▒░ ▓██▄   ▒███   
  ▒██ █░░░██▄▄▄▄██ ▒██░    ▓▓█  ░██░▒▓█  ▄   ▒██ █░░▒▓█  ▄ ▒██▀▀█▄    ▒   ██▒▒▓█  ▄ 
   ▒▀█░   ▓█   ▓██▒░██████▒▒▒█████▓ ░▒████▒   ▒▀█░  ░▒████▒░██▓ ▒██▒▒██████▒▒░▒████▒
   ░ ▐░   ▒▒   ▓▒█░░ ▒░▓  ░░▒▓▒ ▒ ▒ ░░ ▒░ ░   ░ ▐░  ░░ ▒░ ░░ ▒▓ ░▒▓░▒ ▒▓▒ ▒ ░░░ ▒░ ░
   ░ ░░    ▒   ▒▒ ░░ ░ ▒  ░░░▒░ ░ ░  ░ ░  ░   ░ ░░   ░ ░  ░  ░▒ ░ ▒░░ ░▒  ░ ░ ░ ░  ░
     ░░    ░   ▒     ░ ░    ░░░ ░ ░    ░        ░░     ░     ░░   ░ ░  ░  ░     ░   
      ░        ░  ░    ░  ░   ░        ░  ░      ░     ░  ░   ░           ░     ░  ░

           MICROSERVICES INFRASTRUCTURE DEPLOYMENT
           Kong Gateway | Consul | Jaeger | Services
EOF
echo -e "${NC}"

echo -e "${GREEN}Starting complete infrastructure deployment...${NC}"
echo ""

# Function to check if service is healthy
check_service() {
    local url=$1
    local name=$2
    echo -n "Checking $name..."
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${YELLOW}✗${NC}"
        return 1
    fi
}

# Step 1: Deploy Infrastructure
echo -e "${BLUE}[Step 1/5]${NC} Deploying infrastructure components..."
cd infrastructure
./deploy-infrastructure.sh start
cd ..
sleep 10

# Step 2: Build Microservices
echo ""
echo -e "${BLUE}[Step 2/5]${NC} Building microservices..."
docker-compose -f docker-compose.microservices.yml build --parallel

# Step 3: Start Microservices
echo ""
echo -e "${BLUE}[Step 3/5]${NC} Starting microservices..."
docker-compose -f docker-compose.microservices.yml up -d

# Step 4: Wait for services to be healthy
echo ""
echo -e "${BLUE}[Step 4/5]${NC} Waiting for services to be healthy..."
sleep 15

# Check all services
echo ""
echo "Service Health Status:"
echo "----------------------"
check_service "http://localhost:8000" "Kong API Gateway"
check_service "http://localhost:8500/v1/status/leader" "Consul"
check_service "http://localhost:16686/health" "Jaeger"
check_service "http://localhost:8011/health" "Value Architect"
check_service "http://localhost:8012/health" "Value Committer"
check_service "http://localhost:9090" "Prometheus"
check_service "http://localhost:3001" "Grafana"

# Step 5: Register services with Kong
echo ""
echo -e "${BLUE}[Step 5/5]${NC} Configuring API Gateway routes..."

# Add each service to Kong
services=("value-architect:8001" "value-committer:8002" "value-executor:8003" "value-amplifier:8004")

for service in "${services[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"
    
    echo -n "  Registering $name..."
    curl -X POST http://localhost:8001/services \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$name\", \"url\": \"http://$name:$port\"}" \
        > /dev/null 2>&1
    
    curl -X POST http://localhost:8001/services/$name/routes \
        -H "Content-Type: application/json" \
        -d "{\"paths\": [\"/api/$name\"]}" \
        > /dev/null 2>&1
    
    echo -e " ${GREEN}✓${NC}"
done

# Show summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        ✓ Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "🌐 Access Points:"
echo ""
echo "  ${BLUE}API Gateway:${NC}"
echo "    Main:     http://localhost:8000"
echo "    Admin:    http://localhost:8001"
echo ""
echo "  ${BLUE}Service Discovery:${NC}"
echo "    Consul:   http://localhost:8500"
echo ""
echo "  ${BLUE}Tracing:${NC}"
echo "    Jaeger:   http://localhost:16686"
echo ""
echo "  ${BLUE}Monitoring:${NC}"
echo "    Grafana:  http://localhost:3001 (admin/admin)"
echo "    Prometheus: http://localhost:9090"
echo ""
echo "  ${BLUE}Services (via Gateway):${NC}"
echo "    Value Models: http://localhost:8000/api/value-architect/v1/value-models"
echo "    Commitments:  http://localhost:8000/api/value-committer/v1/commitments"
echo ""
echo -e "${YELLOW}Quick Test:${NC}"
echo "  curl http://localhost:8000/api/value-architect/v1/value-models \\"
echo "    -X POST -H 'Content-Type: application/json' \\"
echo "    -d '{\"company_name\": \"Test Corp\", \"industry\": \"SaaS\"}'"
echo ""
echo -e "${GREEN}View distributed trace in Jaeger: http://localhost:16686${NC}"
echo ""
