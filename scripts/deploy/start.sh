#!/bin/bash

# ValueVerse Platform - Development Startup Script

echo "🚀 Starting ValueVerse Platform..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18+ first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"

# Create necessary directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p valueverse/backend/logs
mkdir -p valueverse/data
mkdir -p frontend/public/uploads

# Check for .env file
if [ ! -f valueverse/.env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    if [ -f valueverse/env.example ]; then
        cp valueverse/env.example valueverse/.env
        echo -e "${GREEN}✅ Created .env file. Please update with your API keys.${NC}"
    else
        echo -e "${RED}❌ No env.example file found. Creating basic .env...${NC}"
        cat > valueverse/.env << EOF
DATABASE_URL=postgresql://valueverse:valueverse123@localhost:5432/valueverse
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-change-in-production-$(openssl rand -hex 32)
OPENAI_API_KEY=your-openai-api-key
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
        echo -e "${YELLOW}⚠️  Please update the .env file with your actual API keys${NC}"
    fi
fi

# Start Docker services
echo -e "${BLUE}Starting Docker services...${NC}"
cd valueverse
docker-compose down 2>/dev/null
docker-compose up -d

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be healthy...${NC}"
sleep 5

# Check if PostgreSQL is ready
until docker exec valueverse-db pg_isready -U valueverse > /dev/null 2>&1; do
    echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
    sleep 2
done
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"

# Check if Redis is ready
until docker exec valueverse-redis redis-cli ping > /dev/null 2>&1; do
    echo -e "${YELLOW}Waiting for Redis...${NC}"
    sleep 2
done
echo -e "${GREEN}✅ Redis is ready${NC}"

# Initialize database if needed
echo -e "${BLUE}Checking database initialization...${NC}"
if docker exec valueverse-db psql -U valueverse -d valueverse -c "SELECT 1 FROM tenants LIMIT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database already initialized${NC}"
else
    echo -e "${YELLOW}Initializing database...${NC}"
    docker exec -i valueverse-db psql -U valueverse -d valueverse < backend/schema.sql
    echo -e "${GREEN}✅ Database initialized${NC}"
fi

# Install frontend dependencies if needed
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing frontend dependencies...${NC}"
    npm install
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi

# Start frontend development server
echo -e "${BLUE}Starting frontend development server...${NC}"
npm run dev &
FRONTEND_PID=$!

# Display service URLs
echo -e "\n${GREEN}🎉 ValueVerse Platform is running!${NC}\n"
echo -e "${BLUE}Service URLs:${NC}"
echo -e "  Frontend:    ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:    ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  pgAdmin:     ${GREEN}http://localhost:5050${NC}"
echo -e "    Email:     admin@valueverse.ai"
echo -e "    Password:  admin123"
echo -e ""
echo -e "${BLUE}Database:${NC}"
echo -e "  Host:     localhost"
echo -e "  Port:     5432"
echo -e "  Database: valueverse"
echo -e "  Username: valueverse"
echo -e "  Password: valueverse123"
echo -e ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill $FRONTEND_PID 2>/dev/null
    cd ../valueverse
    docker-compose down
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set up trap for cleanup
trap cleanup INT TERM

# Keep script running
wait $FRONTEND_PID
