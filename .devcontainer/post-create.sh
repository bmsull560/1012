#!/bin/bash

set -e

echo "🚀 Setting up ValueVerse development environment..."

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install --user -r requirements.txt
fi

# Install Node.js dependencies if package.json exists
if [ -f "package.json" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Set up pre-commit hooks if .pre-commit-config.yaml exists
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🔧 Setting up pre-commit hooks..."
    pip3 install --user pre-commit
    pre-commit install
fi

# Initialize the database schema if needed
if [ -f "scripts/init-db.sql" ]; then
    echo "🗄️  Initializing database schema..."
    PGPASSWORD=password psql -h db -U user -d valuedb -f scripts/init-db.sql || true
fi

# Create necessary directories
mkdir -p logs
mkdir -p data
mkdir -p uploads

echo "✅ Development environment setup complete!"
echo ""
echo "📝 Quick Start Commands:"
echo "  Frontend: cd frontend && npm run dev"
echo "  Backend:  cd backend && uvicorn main:app --reload"
echo "  Tests:    pytest"
echo ""
