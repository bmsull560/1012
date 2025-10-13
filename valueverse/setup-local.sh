#!/bin/bash

# ValueVerse Platform - Local Development Setup
# ==============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo "======================================"
echo "ValueVerse Platform - Local Setup"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the valueverse directory"
    exit 1
fi

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo "---------------------------------"

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js is installed ($NODE_VERSION)"
else
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_status "npm is installed ($NPM_VERSION)"
else
    print_error "npm is not installed."
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python is installed ($PYTHON_VERSION)"
else
    print_error "Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

# Check Docker (optional)
if command -v docker &> /dev/null; then
    print_status "Docker is installed (optional - for database)"
else
    print_warning "Docker is not installed. You'll need to set up PostgreSQL and Redis manually."
fi

echo ""

# Step 2: Set up environment file
echo "Step 2: Setting up environment..."
echo "---------------------------------"

if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp env.example .env
    print_status ".env file created"
    print_warning "Please edit .env and add your API keys if you want AI features"
else
    print_status ".env file already exists"
fi

echo ""

# Step 3: Install backend dependencies
echo "Step 3: Setting up backend..."
echo "-----------------------------"

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_info "Installing backend dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

print_status "Backend dependencies installed"

# Deactivate for now
deactivate

cd ..
echo ""

# Step 4: Install frontend dependencies
echo "Step 4: Setting up frontend..."
echo "------------------------------"

cd frontend

print_info "Installing frontend dependencies..."
npm install

print_status "Frontend dependencies installed"

cd ..
echo ""

# Step 5: Set up databases (if Docker is available)
if command -v docker &> /dev/null; then
    echo "Step 5: Setting up databases..."
    echo "-------------------------------"
    
    print_info "Starting PostgreSQL and Redis with Docker..."
    
    # Start only database services
    docker-compose up -d postgres redis 2>/dev/null || {
        print_warning "Could not start Docker services. You may need to run: docker-compose up -d postgres redis"
    }
    
    # Wait for databases to be ready
    print_info "Waiting for databases to be ready..."
    sleep 5
    
    print_status "Database services started"
else
    echo "Step 5: Database setup (manual required)..."
    echo "-------------------------------------------"
    print_warning "Please ensure PostgreSQL and Redis are running locally"
    print_info "PostgreSQL should be on port 5432"
    print_info "Redis should be on port 6379"
fi

echo ""

# Step 6: Create run scripts
echo "Step 6: Creating run scripts..."
echo "-------------------------------"

# Create backend run script
cat > run-backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
echo "Starting ValueVerse Backend on http://localhost:8000"
echo "API Docs will be available at http://localhost:8000/api/v1/docs"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
EOF

chmod +x run-backend.sh
print_status "Created run-backend.sh"

# Create frontend run script
cat > run-frontend.sh << 'EOF'
#!/bin/bash
cd frontend
echo "Starting ValueVerse Frontend on http://localhost:3000"
npm run dev
EOF

chmod +x run-frontend.sh
print_status "Created run-frontend.sh"

# Create combined run script
cat > run-all.sh << 'EOF'
#!/bin/bash

# Function to cleanup background processes on exit
cleanup() {
    echo "Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

echo "Starting ValueVerse Platform..."
echo "================================"
echo ""

# Start backend in background
echo "Starting backend..."
./run-backend.sh &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in background
echo "Starting frontend..."
./run-frontend.sh &
FRONTEND_PID=$!

echo ""
echo "================================"
echo "ValueVerse Platform is starting!"
echo "================================"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/v1/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for background processes
wait
EOF

chmod +x run-all.sh
print_status "Created run-all.sh"

echo ""
echo "======================================"
echo -e "${GREEN}✨ Setup Complete!${NC}"
echo "======================================"
echo ""
echo "To run the platform:"
echo ""
echo "Option 1: Run everything together"
echo "  ./run-all.sh"
echo ""
echo "Option 2: Run services separately (in different terminals)"
echo "  Terminal 1: ./run-backend.sh"
echo "  Terminal 2: ./run-frontend.sh"
echo ""
echo "Access the platform at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/api/v1/docs"
echo "  Agent Demo: http://localhost:3000/agent-demo"
echo "  Main Demo: http://localhost:3000/demo"
echo ""

# Check if .env needs API keys
if grep -q "OPENAI_API_KEY=$" .env 2>/dev/null || grep -q "ANTHROPIC_API_KEY=$" .env 2>/dev/null; then
    print_warning "Don't forget to add your AI API keys to .env for full functionality"
fi

echo ""
read -p "Would you like to start the platform now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./run-all.sh
fi
