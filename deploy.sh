#!/bin/bash

# ValueVerse One-Command Deployment Script
# This script provides a cross-platform deployment solution

set -e  # Exit on error

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
print_banner() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   ValueVerse Local Deployment v1.0    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
check_dependencies() {
    echo -e "${BLUE}→ Checking dependencies...${NC}"
    
    if ! command_exists docker; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        echo "Please install Docker from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        echo -e "${RED}✗ Docker Compose is not installed${NC}"
        echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}✗ Docker is not running${NC}"
        echo "Please start Docker and try again"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All dependencies are installed${NC}"
    echo ""
}

# Setup environment
setup_environment() {
    echo -e "${BLUE}→ Setting up environment...${NC}"
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file from template${NC}"
        echo -e "${YELLOW}⚠ Please update .env with your API keys if needed${NC}"
    else
        echo -e "${YELLOW}⚠ .env file already exists, skipping${NC}"
    fi
    
    echo ""
}

# Start services
start_services() {
    echo -e "${BLUE}→ Starting services...${NC}"
    
    # Use docker-compose or docker compose based on what's available
    if command_exists docker-compose; then
        docker-compose up -d --build
    else
        docker compose up -d --build
    fi
    
    echo -e "${GREEN}✓ Services started${NC}"
    echo ""
}

# Wait for services
wait_for_services() {
    echo -e "${BLUE}→ Waiting for services to be ready...${NC}"
    
    # Wait for database
    echo -e "${BLUE}  Waiting for database...${NC}"
    for i in {1..30}; do
        if command_exists docker-compose; then
            if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
                echo -e "${GREEN}  ✓ Database is ready${NC}"
                break
            fi
        else
            if docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
                echo -e "${GREEN}  ✓ Database is ready${NC}"
                break
            fi
        fi
        sleep 1
    done
    
    # Wait for backend
    echo -e "${BLUE}  Waiting for backend...${NC}"
    for i in {1..60}; do
        if curl -sf http://localhost:8000/health >/dev/null 2>&1 || curl -sf http://localhost:8000/docs >/dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Backend is ready${NC}"
            break
        fi
        sleep 1
    done
    
    # Wait for frontend
    echo -e "${BLUE}  Waiting for frontend...${NC}"
    for i in {1..60}; do
        if curl -sf http://localhost:3000 >/dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Frontend is ready${NC}"
            break
        fi
        sleep 1
    done
    
    echo ""
}

# Health check
health_check() {
    echo -e "${BLUE}→ Running health checks...${NC}"
    
    DB_STATUS="${RED}✗ Unhealthy${NC}"
    BACKEND_STATUS="${RED}✗ Unhealthy${NC}"
    FRONTEND_STATUS="${RED}✗ Unhealthy${NC}"
    
    if command_exists docker-compose; then
        docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1 && DB_STATUS="${GREEN}✓ Healthy${NC}"
    else
        docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1 && DB_STATUS="${GREEN}✓ Healthy${NC}"
    fi
    
    curl -sf http://localhost:8000/health >/dev/null 2>&1 && BACKEND_STATUS="${GREEN}✓ Healthy${NC}" || BACKEND_STATUS="${YELLOW}⚠ Not responding${NC}"
    curl -sf http://localhost:3000 >/dev/null 2>&1 && FRONTEND_STATUS="${GREEN}✓ Healthy${NC}" || FRONTEND_STATUS="${YELLOW}⚠ Not responding${NC}"
    
    echo -e "  ${BLUE}Database:${NC} $DB_STATUS"
    echo -e "  ${BLUE}Backend:${NC} $BACKEND_STATUS"
    echo -e "  ${BLUE}Frontend:${NC} $FRONTEND_STATUS"
    echo ""
}

# Print success message
print_success() {
    echo -e "${GREEN}✓ Deployment complete!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🌐 Frontend:${NC} http://localhost:3000"
    echo -e "${GREEN}🔌 Backend API:${NC} http://localhost:8000"
    echo -e "${GREEN}📚 API Docs:${NC} http://localhost:8000/docs"
    echo -e "${GREEN}🗄️  Database:${NC} localhost:5432"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}📋 Useful commands:${NC}"
    echo "  make logs        - View application logs"
    echo "  make status      - Check service status"
    echo "  make restart     - Restart all services"
    echo "  make clean       - Stop and remove everything"
    echo "  ./deploy.sh stop - Stop all services"
    echo ""
}

# Stop services
stop_services() {
    echo -e "${BLUE}→ Stopping services...${NC}"
    
    if command_exists docker-compose; then
        docker-compose down
    else
        docker compose down
    fi
    
    echo -e "${GREEN}✓ Services stopped${NC}"
}

# Clean everything
clean_all() {
    echo -e "${RED}→ Cleaning up (this will remove all data)...${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command_exists docker-compose; then
            docker-compose down -v --remove-orphans
        else
            docker compose down -v --remove-orphans
        fi
        echo -e "${GREEN}✓ Cleanup complete${NC}"
    else
        echo "Cancelled"
    fi
}

# Main deployment flow
main() {
    case "${1:-deploy}" in
        deploy)
            print_banner
            check_dependencies
            setup_environment
            start_services
            wait_for_services
            health_check
            print_success
            ;;
        stop)
            stop_services
            ;;
        clean)
            clean_all
            ;;
        status)
            if command_exists docker-compose; then
                docker-compose ps
            else
                docker compose ps
            fi
            ;;
        logs)
            if command_exists docker-compose; then
                docker-compose logs -f
            else
                docker compose logs -f
            fi
            ;;
        help|*)
            echo "ValueVerse Deployment Script"
            echo ""
            echo "Usage: ./deploy.sh [command]"
            echo ""
            echo "Commands:"
            echo "  deploy  - Deploy the application (default)"
            echo "  stop    - Stop all services"
            echo "  clean   - Remove all containers and volumes"
            echo "  status  - Show service status"
            echo "  logs    - Show service logs"
            echo "  help    - Show this help message"
            echo ""
            ;;
    esac
}

# Run main function
main "$@"
