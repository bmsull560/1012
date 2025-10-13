#!/bin/bash

# Clean Cache Files Script for ValueVerse
# This script removes all cache files and directories from the repository

echo "🧹 Cleaning cache files from ValueVerse repository..."

# Python cache cleanup
echo "Removing Python __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "Removing .ruff_cache..."
rm -rf .ruff_cache

echo "Removing .pytest_cache..."
rm -rf .pytest_cache

echo "Removing Python .pyc files..."
find . -name "*.pyc" -delete 2>/dev/null

echo "Removing Python .pyo files..."
find . -name "*.pyo" -delete 2>/dev/null

echo "Removing Python .pyd files..."
find . -name "*.pyd" -delete 2>/dev/null

# Node/Next.js cache cleanup
echo "Removing .next build cache..."
rm -rf frontend/.next
rm -rf archived_frontend/.next

echo "Removing node_modules cache..."
rm -rf node_modules/.cache
rm -rf frontend/node_modules/.cache
rm -rf archived_frontend/node_modules/.cache

# TypeScript cache
echo "Removing TypeScript build info..."
find . -name "*.tsbuildinfo" -delete 2>/dev/null

# Other common cache directories
echo "Removing .parcel-cache..."
rm -rf .parcel-cache

echo "Removing .turbo cache..."
rm -rf .turbo

echo "Removing .cache directories..."
find . -type d -name ".cache" -exec rm -rf {} + 2>/dev/null

# Build artifacts
echo "Removing dist directories..."
rm -rf dist
rm -rf frontend/dist
rm -rf archived_frontend/dist

echo "Removing build directories..."
rm -rf build
rm -rf frontend/build
rm -rf archived_frontend/build

echo "Removing out directories (Next.js)..."
rm -rf out
rm -rf frontend/out
rm -rf archived_frontend/out

# IDE cache (optional - uncomment if you want to clean these too)
# echo "Removing .vscode cache..."
# rm -rf .vscode/.cache

# Docker (be careful with this - it won't affect running containers)
# echo "Removing Docker build cache..."
# docker builder prune -f 2>/dev/null

# Coverage reports
echo "Removing coverage reports..."
rm -rf coverage
rm -rf .coverage
rm -rf htmlcov
rm -rf .nyc_output

# Temporary files
echo "Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null
find . -name "*.temp" -delete 2>/dev/null
find . -name "*.swp" -delete 2>/dev/null
find . -name "*.swo" -delete 2>/dev/null
find . -name "*~" -delete 2>/dev/null
find . -name ".DS_Store" -delete 2>/dev/null
find . -name "Thumbs.db" -delete 2>/dev/null

# Log files (optional - uncomment if you want to clean logs)
# echo "Removing log files..."
# find . -name "*.log" -delete 2>/dev/null
# rm -rf logs

echo "✅ Cache cleanup complete!"

# Show disk usage before and after
echo ""
echo "📊 Repository size after cleanup:"
du -sh .

# Count remaining files
echo ""
echo "📁 File count:"
find . -type f ! -path "./.git/*" ! -path "./node_modules/*" ! -path "./.venv/*" ! -path "./venv/*" | wc -l

echo ""
echo "🎉 All cache files have been removed!"
echo ""
echo "Note: The following were NOT removed (they're not cache):"
echo "  - .venv/ and venv/ (Python virtual environments)"
echo "  - node_modules/ (Node.js dependencies)"
echo "  - .git/ (Git repository)"
echo ""
echo "To reinstall dependencies after cleanup:"
echo "  - Python: pip install -r requirements.txt"
echo "  - Frontend: cd frontend && npm install"
