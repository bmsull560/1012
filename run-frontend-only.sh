#!/bin/bash

# ValueVerse - Run Frontend Only (Backend should be started separately)
# =====================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "ValueVerse - Frontend Launch"
echo -e "======================================${NC}"
echo ""

# Check if backend is running
if curl -f http://localhost:8000/health &> /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running on port 8000${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Backend doesn't appear to be running on port 8000${NC}"
    echo -e "${YELLOW}  You may need to start it separately or use Docker${NC}"
    echo ""
    echo "Options to start backend:"
    echo "1. Use Docker: docker-compose up -d"
    echo "2. Install PostgreSQL: sudo apt-get install postgresql libpq-dev"
    echo "3. Use the existing Makefile: make deploy"
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Setup and start frontend
echo ""
echo -e "${BLUE}Setting up frontend...${NC}"
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install --legacy-peer-deps
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

# Start frontend
echo ""
echo -e "${BLUE}Starting frontend...${NC}"
npm run dev &
FRONTEND_PID=$!

# Give it a moment to start
sleep 3

echo ""
echo -e "${GREEN}======================================"
echo "✨ ValueVerse Frontend is running!"
echo -e "======================================${NC}"
echo ""
echo "Access points:"
echo -e "${BLUE}  • Homepage: http://localhost:3000${NC}"
echo -e "${BLUE}  • Agent Demo: http://localhost:3000/agent-demo${NC}"
echo -e "${BLUE}  • Main Demo: http://localhost:3000/demo${NC}"
echo ""
if curl -f http://localhost:8000/health &> /dev/null 2>&1; then
    echo -e "${GREEN}  • Backend API: http://localhost:8000${NC}"
    echo -e "${GREEN}  • API Docs: http://localhost:8000/docs${NC}"
else
    echo -e "${RED}  • Backend: Not running (some features may not work)${NC}"
fi
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down frontend..."
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit
}

trap cleanup EXIT INT TERM

# Wait
wait $FRONTEND_PID
