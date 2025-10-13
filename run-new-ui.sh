#!/bin/bash

# ValueVerse - Run New UI with Existing Backend
# ==============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "ValueVerse - New UI Launch"
echo -e "======================================${NC}"
echo ""

# Check if backend is running
if curl -f http://localhost:8000/health &> /dev/null; then
    echo -e "${GREEN}✓ Backend is already running${NC}"
else
    echo -e "${YELLOW}Starting backend...${NC}"
    cd src/backend
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt --quiet
    else
        source venv/bin/activate
    fi
    python main.py &
    BACKEND_PID=$!
    cd ../..
    sleep 3
    echo -e "${GREEN}✓ Backend started${NC}"
fi

# Install frontend dependencies if needed
echo ""
echo -e "${BLUE}Setting up new frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install --legacy-peer-deps
fi

echo -e "${GREEN}✓ Frontend ready${NC}"
echo ""

# Start frontend
echo -e "${BLUE}Starting new UI...${NC}"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}======================================"
echo "✨ New ValueVerse UI is running!"
echo -e "======================================${NC}"
echo ""
echo "Access points:"
echo -e "${BLUE}  • New UI: http://localhost:3000${NC}"
echo -e "${BLUE}  • Agent Demo: http://localhost:3000/agent-demo${NC}"
echo -e "${BLUE}  • Main Demo: http://localhost:3000/demo${NC}"
echo -e "${BLUE}  • Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}  • API Docs: http://localhost:8000/docs${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down..."
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    exit
}

trap cleanup EXIT INT TERM

# Wait
wait
