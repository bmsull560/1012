.PHONY: deploy clean status logs help restart rebuild test health check-deps

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

## deploy: 🚀 Complete one-command deployment (setup + start)
deploy: check-deps
	@echo "$(BLUE)╔════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║   ValueVerse Local Deployment v1.0    ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════╝$(NC)"
	@echo ""
	@$(MAKE) --no-print-directory setup
	@$(MAKE) --no-print-directory start
	@$(MAKE) --no-print-directory health
	@echo ""
	@echo "$(GREEN)✓ Deployment complete!$(NC)"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(GREEN)🌐 Frontend:$(NC) http://localhost:3000"
	@echo "$(GREEN)🔌 Backend API:$(NC) http://localhost:8000"
	@echo "$(GREEN)📚 API Docs:$(NC) http://localhost:8000/docs"
	@echo "$(GREEN)🗄️  Database:$(NC) localhost:5432"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(YELLOW)📋 Useful commands:$(NC)"
	@echo "  make logs     - View application logs"
	@echo "  make status   - Check service status"
	@echo "  make restart  - Restart all services"
	@echo "  make clean    - Stop and remove everything"
	@echo ""

## setup: Initialize environment and configuration
setup:
	@echo "$(BLUE)→ Setting up environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env && \
		echo "$(GREEN)✓ Created .env file from template$(NC)"; \
	else \
		echo "$(YELLOW)⚠ .env file already exists, skipping$(NC)"; \
	fi
	@echo "$(GREEN)✓ Environment setup complete$(NC)"
	@echo ""

## start: Start all services with Docker Compose
start:
	@echo "$(BLUE)→ Starting services...$(NC)"
	@docker-compose up -d --build
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo ""
	@echo "$(BLUE)→ Waiting for services to be ready...$(NC)"
	@sleep 5
	@echo ""

## stop: Stop all running services
stop:
	@echo "$(BLUE)→ Stopping services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

## restart: Restart all services
restart: stop start
	@echo "$(GREEN)✓ Services restarted$(NC)"

## rebuild: Rebuild and restart all services
rebuild:
	@echo "$(BLUE)→ Rebuilding services...$(NC)"
	@docker-compose down
	@docker-compose build --no-cache
	@docker-compose up -d
	@echo "$(GREEN)✓ Services rebuilt and restarted$(NC)"

## clean: Stop and remove all containers, volumes, and generated files
clean:
	@echo "$(RED)→ Cleaning up...$(NC)"
	@docker-compose down -v --remove-orphans
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

## logs: View logs from all services
logs:
	@docker-compose logs -f

## logs-backend: View backend logs only
logs-backend:
	@docker-compose logs -f backend

## logs-frontend: View frontend logs only
logs-frontend:
	@docker-compose logs -f frontend

## logs-db: View database logs only
logs-db:
	@docker-compose logs -f postgres

## status: Check status of all services
status:
	@echo "$(BLUE)╔════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║        Service Status Check            ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════╝$(NC)"
	@echo ""
	@docker-compose ps
	@echo ""

## health: Check health of all services
health:
	@echo "$(BLUE)→ Running health checks...$(NC)"
	@echo ""
	@printf "$(BLUE)Database:$(NC) "
	@if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(RED)✗ Unhealthy$(NC)"; \
	fi
	@printf "$(BLUE)Backend:$(NC) "
	@if curl -sf http://localhost:8000/health > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Not responding (may still be starting)$(NC)"; \
	fi
	@printf "$(BLUE)Frontend:$(NC) "
	@if curl -sf http://localhost:3000 > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Healthy$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Not responding (may still be starting)$(NC)"; \
	fi
	@echo ""

## check-deps: Check if required dependencies are installed
check-deps:
	@echo "$(BLUE)→ Checking dependencies...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)✗ Docker is not installed. Please install Docker first.$(NC)"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "$(RED)✗ Docker Compose is not installed. Please install Docker Compose first.$(NC)"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "$(RED)✗ Docker is not running. Please start Docker first.$(NC)"; exit 1; }
	@echo "$(GREEN)✓ All dependencies are installed$(NC)"
	@echo ""

## test: Run test suite
test:
	@echo "$(BLUE)→ Running tests...$(NC)"
	@docker-compose exec backend pytest
	@echo "$(GREEN)✓ Tests complete$(NC)"

## shell-backend: Open a shell in the backend container
shell-backend:
	@docker-compose exec backend /bin/bash

## shell-frontend: Open a shell in the frontend container
shell-frontend:
	@docker-compose exec frontend /bin/sh

## shell-db: Open PostgreSQL shell
shell-db:
	@docker-compose exec postgres psql -U postgres -d valueverse

## help: Show this help message
help:
	@echo "$(BLUE)╔════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║   ValueVerse Deployment Commands      ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Quick Start:$(NC)"
	@echo "  $(YELLOW)make deploy$(NC)  - Complete one-command deployment"
	@echo ""
	@echo "$(GREEN)Available Commands:$(NC)"
	@sed -n 's/^##//p' Makefile | column -t -s ':' | sed -e 's/^/  /'
	@echo ""
