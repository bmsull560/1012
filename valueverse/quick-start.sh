#!/bin/bash

# ValueVerse Quick Start - Simplified Local Setup
# ================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "ValueVerse Platform - Quick Start"
echo -e "======================================${NC}"
echo ""

# Step 1: Backend Setup
echo -e "${GREEN}Step 1: Setting up Backend...${NC}"
cd backend

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip --quiet
echo "Installing backend dependencies (this may take a minute)..."
pip install fastapi uvicorn pydantic sqlalchemy aiofiles python-socketio --quiet
echo -e "${GREEN}✓ Backend ready${NC}"

deactivate
cd ..

# Step 2: Frontend Setup
echo ""
echo -e "${GREEN}Step 2: Setting up Frontend...${NC}"
cd frontend

# Install minimal dependencies
echo "Installing frontend dependencies..."
npm install --legacy-peer-deps

echo -e "${GREEN}✓ Frontend ready${NC}"
cd ..

# Step 3: Create environment file
echo ""
echo -e "${GREEN}Step 3: Creating environment file...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
DEBUG=true
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///./valueverse.db
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
EOF
    echo -e "${GREEN}✓ Environment configured${NC}"
else
    echo -e "${YELLOW}✓ Environment file already exists${NC}"
fi

# Step 4: Create simple run script
echo ""
echo -e "${GREEN}Step 4: Creating run script...${NC}"

cat > run.sh << 'EOF'
#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting ValueVerse Platform...${NC}"
echo ""

# Start backend
echo "Starting backend server..."
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}======================================"
echo "ValueVerse Platform is running!"
echo "======================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Demo Pages:"
echo "  • Agent Demo: http://localhost:3000/agent-demo"
echo "  • Main Demo: http://localhost:3000/demo"
echo ""
echo "Press Ctrl+C to stop all services${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Wait for processes
wait
EOF

chmod +x run.sh

echo -e "${GREEN}✓ Run script created${NC}"

echo ""
echo -e "${GREEN}======================================"
echo "✨ Setup Complete!"
echo -e "======================================${NC}"
echo ""
echo "To start the platform, run:"
echo -e "${BLUE}  ./run.sh${NC}"
echo ""
echo "Then access:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo ""

read -p "Start the platform now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./run.sh
fi
