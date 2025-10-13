#!/bin/bash

# ValueVerse Platform Quick Start Script
# This script sets up and starts the entire platform

set -e  # Exit on error

echo "🚀 Starting ValueVerse Platform Setup..."
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check prerequisites
echo ""
echo "Checking prerequisites..."
echo "------------------------"

# Check Docker
if command -v docker &> /dev/null; then
    print_status "Docker is installed ($(docker --version))"
else
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    print_status "Docker Compose is installed ($(docker-compose --version))"
else
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker daemon is running
if docker info &> /dev/null; then
    print_status "Docker daemon is running"
else
    print_error "Docker daemon is not running. Please start Docker."
    exit 1
fi

# Create .env file if it doesn't exist
echo ""
echo "Setting up environment..."
echo "------------------------"

if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    cat > .env << EOF
# ValueVerse Platform Environment Variables
# ==========================================

# Application
DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)

# Database
DATABASE_URL=postgresql+asyncpg://valueverse:valueverse@postgres:5432/valueverse

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# AI Services (Add your API keys here)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
TOGETHER_API_KEY=

# Vector Store
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=valueverse

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
EOF
    print_status ".env file created"
    print_warning "Please edit .env and add your API keys before running the platform"
    echo ""
    read -p "Press Enter to continue after adding API keys, or Ctrl+C to exit..."
else
    print_status ".env file exists"
fi

# Stop any existing containers
echo ""
echo "Cleaning up existing containers..."
echo "---------------------------------"
docker-compose down 2>/dev/null || true
print_status "Cleanup complete"

# Build and start services
echo ""
echo "Building and starting services..."
echo "---------------------------------"

# Start infrastructure services first
print_status "Starting PostgreSQL..."
docker-compose up -d postgres

print_status "Starting Redis..."
docker-compose up -d redis

# Wait for databases to be ready
echo ""
print_status "Waiting for databases to be ready..."
sleep 10

# Start backend services
print_status "Starting Backend API..."
docker-compose up -d backend

print_status "Starting Celery Worker..."
docker-compose up -d celery

# Start frontend
print_status "Starting Frontend..."
docker-compose up -d frontend

# Wait for services to be fully up
echo ""
print_status "Waiting for services to initialize..."
sleep 15

# Check service health
echo ""
echo "Checking service health..."
echo "-------------------------"

# Check backend health
if curl -f http://localhost:8000/health &> /dev/null; then
    print_status "Backend API is healthy"
else
    print_warning "Backend API health check failed (this may be normal during first startup)"
fi

# Check frontend
if curl -f http://localhost:3000 &> /dev/null; then
    print_status "Frontend is accessible"
else
    print_warning "Frontend is not yet accessible (may still be building)"
fi

# Print access information
echo ""
echo "======================================="
echo -e "${GREEN}✨ ValueVerse Platform is starting!${NC}"
echo "======================================="
echo ""
echo "Access the platform at:"
echo "  Frontend:    http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs:    http://localhost:8000/api/v1/docs"
echo ""
echo "Default credentials:"
echo "  Email:    admin@valueverse.ai"
echo "  Password: ChangeMe123!"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f [service]"
echo "  Stop platform:    docker-compose down"
echo "  Restart service:  docker-compose restart [service]"
echo "  View status:      docker-compose ps"
echo ""
echo "Services: postgres, redis, backend, celery, frontend"
echo ""
print_status "Setup complete! The platform may take a few more moments to be fully ready."
echo ""

# Option to view logs
read -p "Would you like to view the logs? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
fi
