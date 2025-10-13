# ValueVerse One-Command Deployment Script for Windows
# PowerShell Script

param(
    [Parameter(Position=0)]
    [string]$Command = "deploy"
)

# Colors for output
function Write-Blue { Write-Host $args -ForegroundColor Blue }
function Write-Green { Write-Host $args -ForegroundColor Green }
function Write-Yellow { Write-Host $args -ForegroundColor Yellow }
function Write-Red { Write-Host $args -ForegroundColor Red }

# Print banner
function Print-Banner {
    Write-Blue "╔════════════════════════════════════════╗"
    Write-Blue "║   ValueVerse Local Deployment v1.0    ║"
    Write-Blue "╚════════════════════════════════════════╝"
    Write-Host ""
}

# Check if command exists
function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Check dependencies
function Check-Dependencies {
    Write-Blue "→ Checking dependencies..."
    
    if (!(Test-CommandExists "docker")) {
        Write-Red "✗ Docker is not installed"
        Write-Host "Please install Docker Desktop from: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    }
    
    $dockerRunning = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Red "✗ Docker is not running"
        Write-Host "Please start Docker Desktop and try again"
        exit 1
    }
    
    if (!(Test-CommandExists "docker-compose") -and !(docker compose version 2>&1)) {
        Write-Red "✗ Docker Compose is not available"
        Write-Host "Please ensure Docker Compose is installed (usually included with Docker Desktop)"
        exit 1
    }
    
    Write-Green "✓ All dependencies are installed"
    Write-Host ""
}

# Setup environment
function Setup-Environment {
    Write-Blue "→ Setting up environment..."
    
    if (!(Test-Path .env)) {
        Copy-Item .env.example .env
        Write-Green "✓ Created .env file from template"
        Write-Yellow "⚠ Please update .env with your API keys if needed"
    } else {
        Write-Yellow "⚠ .env file already exists, skipping"
    }
    
    Write-Host ""
}

# Start services
function Start-Services {
    Write-Blue "→ Starting services..."
    
    if (Test-CommandExists "docker-compose") {
        docker-compose up -d --build
    } else {
        docker compose up -d --build
    }
    
    Write-Green "✓ Services started"
    Write-Host ""
}

# Wait for services
function Wait-ForServices {
    Write-Blue "→ Waiting for services to be ready..."
    
    # Wait for database
    Write-Blue "  Waiting for database..."
    $maxAttempts = 30
    for ($i = 0; $i -lt $maxAttempts; $i++) {
        if (Test-CommandExists "docker-compose") {
            $result = docker-compose exec -T postgres pg_isready -U postgres 2>&1
        } else {
            $result = docker compose exec -T postgres pg_isready -U postgres 2>&1
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Green "  ✓ Database is ready"
            break
        }
        Start-Sleep -Seconds 1
    }
    
    # Wait for backend
    Write-Blue "  Waiting for backend..."
    $maxAttempts = 60
    for ($i = 0; $i -lt $maxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Green "  ✓ Backend is ready"
                break
            }
        } catch {
            # Try docs endpoint as fallback
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 1 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Green "  ✓ Backend is ready"
                    break
                }
            } catch {}
        }
        Start-Sleep -Seconds 1
    }
    
    # Wait for frontend
    Write-Blue "  Waiting for frontend..."
    for ($i = 0; $i -lt $maxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Green "  ✓ Frontend is ready"
                break
            }
        } catch {}
        Start-Sleep -Seconds 1
    }
    
    Write-Host ""
}

# Health check
function Health-Check {
    Write-Blue "→ Running health checks..."
    
    $dbStatus = "✗ Unhealthy"
    $backendStatus = "✗ Unhealthy"
    $frontendStatus = "✗ Unhealthy"
    
    # Check database
    if (Test-CommandExists "docker-compose") {
        $result = docker-compose exec -T postgres pg_isready -U postgres 2>&1
    } else {
        $result = docker compose exec -T postgres pg_isready -U postgres 2>&1
    }
    if ($LASTEXITCODE -eq 0) {
        $dbStatus = "✓ Healthy"
    }
    
    # Check backend
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendStatus = "✓ Healthy"
        }
    } catch {
        $backendStatus = "⚠ Not responding"
    }
    
    # Check frontend
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $frontendStatus = "✓ Healthy"
        }
    } catch {
        $frontendStatus = "⚠ Not responding"
    }
    
    Write-Host "  Database: $dbStatus"
    Write-Host "  Backend: $backendStatus"
    Write-Host "  Frontend: $frontendStatus"
    Write-Host ""
}

# Print success message
function Print-Success {
    Write-Green "✓ Deployment complete!"
    Write-Blue "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Green "🌐 Frontend: http://localhost:3000"
    Write-Green "🔌 Backend API: http://localhost:8000"
    Write-Green "📚 API Docs: http://localhost:8000/docs"
    Write-Green "🗄️  Database: localhost:5432"
    Write-Blue "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host ""
    Write-Yellow "📋 Useful commands:"
    Write-Host "  .\deploy.ps1 logs     - View application logs"
    Write-Host "  .\deploy.ps1 status   - Check service status"
    Write-Host "  .\deploy.ps1 stop     - Stop all services"
    Write-Host "  .\deploy.ps1 clean    - Remove everything"
    Write-Host ""
}

# Stop services
function Stop-Services {
    Write-Blue "→ Stopping services..."
    
    if (Test-CommandExists "docker-compose") {
        docker-compose down
    } else {
        docker compose down
    }
    
    Write-Green "✓ Services stopped"
}

# Clean everything
function Clean-All {
    Write-Red "→ Cleaning up (this will remove all data)..."
    $confirmation = Read-Host "Are you sure? (y/N)"
    
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        if (Test-CommandExists "docker-compose") {
            docker-compose down -v --remove-orphans
        } else {
            docker compose down -v --remove-orphans
        }
        Write-Green "✓ Cleanup complete"
    } else {
        Write-Host "Cancelled"
    }
}

# Show logs
function Show-Logs {
    if (Test-CommandExists "docker-compose") {
        docker-compose logs -f
    } else {
        docker compose logs -f
    }
}

# Show status
function Show-Status {
    if (Test-CommandExists "docker-compose") {
        docker-compose ps
    } else {
        docker compose ps
    }
}

# Show help
function Show-Help {
    Write-Host "ValueVerse Deployment Script for Windows"
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 [command]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  deploy  - Deploy the application (default)"
    Write-Host "  stop    - Stop all services"
    Write-Host "  clean   - Remove all containers and volumes"
    Write-Host "  status  - Show service status"
    Write-Host "  logs    - Show service logs"
    Write-Host "  help    - Show this help message"
    Write-Host ""
}

# Main function
function Main {
    switch ($Command.ToLower()) {
        "deploy" {
            Print-Banner
            Check-Dependencies
            Setup-Environment
            Start-Services
            Wait-ForServices
            Health-Check
            Print-Success
        }
        "stop" {
            Stop-Services
        }
        "clean" {
            Clean-All
        }
        "status" {
            Show-Status
        }
        "logs" {
            Show-Logs
        }
        "help" {
            Show-Help
        }
        default {
            Show-Help
        }
    }
}

# Run main function
Main
