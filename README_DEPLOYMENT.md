# 🚀 ValueVerse Platform - Complete Deployment Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Service Documentation](#service-documentation)
- [Troubleshooting](#troubleshooting)
- [Development Guide](#development-guide)
- [Production Deployment](#production-deployment)
- [Backup & Restore](#backup--restore)

## 🎯 Overview

ValueVerse is an enterprise-grade B2B SaaS platform featuring AI-powered value creation agents, comprehensive billing system, and real-time analytics. This guide enables you to deploy the entire platform locally with a single command.

### Key Features
- **4 AI Agents**: Value Architect, Committer, Executor, and Amplifier
- **Microservices Architecture**: 6 core services + supporting infrastructure
- **Real-time Processing**: WebSocket connections and event-driven architecture
- **Enterprise Billing**: Usage-based billing with Stripe integration
- **Complete Observability**: Distributed tracing, metrics, and logging

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Next.js UI :3000]
    end
    
    subgraph "API Gateway"
        Kong[Kong Gateway :8000/8001]
    end
    
    subgraph "Microservices"
        VA[Value Architect :8011]
        VC[Value Committer :8012]
        VE[Value Executor :8013]
        VM[Value Amplifier :8014]
        CE[Calculation Engine :8015]
        NS[Notification Service :8016]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL :5432)]
        Redis[(Redis :6379)]
        RMQ[RabbitMQ :5672/15672]
    end
    
    subgraph "Infrastructure"
        Consul[Consul :8500]
        Jaeger[Jaeger :16686]
        Prometheus[Prometheus :9090]
        Grafana[Grafana :3001]
    end
    
    UI --> Kong
    Kong --> VA
    Kong --> VC
    Kong --> VE
    Kong --> VM
    
    VA --> PG
    VA --> Redis
    VC --> PG
    VE --> RMQ
    VM --> NS
    
    Microservices --> Consul
    Microservices --> Jaeger
    Prometheus --> Microservices
    Grafana --> Prometheus
```

## 📦 Prerequisites

### Required Software
| Software | Minimum Version | Recommended Version | Check Command |
|----------|----------------|-------------------|---------------|
| **Docker** | 20.10.0 | 24.0.0+ | `docker --version` |
| **Docker Compose** | 2.0.0 | 2.20.0+ | `docker compose version` |
| **Git** | 2.25.0 | 2.40.0+ | `git --version` |
| **Make** (optional) | 3.81 | 4.3+ | `make --version` |

### System Requirements
- **RAM**: Minimum 8GB (16GB recommended)
- **CPU**: 4+ cores recommended
- **Disk**: 20GB free space
- **OS**: Linux, macOS, or Windows with WSL2

### Network Ports
Ensure these ports are available:
- **3000**: Frontend UI
- **3001**: Grafana
- **5432**: PostgreSQL
- **5672**: RabbitMQ
- **6379**: Redis
- **8000-8001**: Kong API Gateway
- **8011-8016**: Microservices
- **8500**: Consul
- **9090**: Prometheus
- **15672**: RabbitMQ Management
- **16686**: Jaeger UI

## 🚀 Quick Start

### One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/valueverse/platform.git
cd platform

# Deploy everything with one command
./deploy.sh

# Or using Make
make deploy
```

**That's it!** The platform will be available at:
- **Main Application**: http://localhost:3000
- **Admin Login**: admin@valueverse.ai / admin123

## 📖 Detailed Setup

### Step 1: Environment Configuration

```bash
# Copy environment templates
cp .env.example .env
cp frontend/.env.example frontend/.env.local
cp billing-system/.env.example billing-system/.env

# Edit .env with your configurations (optional)
nano .env
```

### Step 2: Manual Deployment (Alternative)

```bash
# 1. Start infrastructure services
docker compose -f docker-compose.infrastructure.yml up -d

# 2. Wait for infrastructure to be ready
./scripts/wait-for-infrastructure.sh

# 3. Start microservices
docker compose -f docker-compose.services.yml up -d

# 4. Start frontend
docker compose -f docker-compose.frontend.yml up -d

# 5. Run database migrations
./scripts/run-migrations.sh

# 6. Seed sample data
./scripts/seed-data.sh
```

### Step 3: Verify Deployment

```bash
# Check all services health
./scripts/health-check.sh

# Or manually verify
curl http://localhost:8011/health  # Should return {"status":"healthy"}
curl http://localhost:3000          # Should load the UI
```

## 🔧 Environment Variables

### Core Configuration
```bash
# Application
NODE_ENV=development                    # Environment: development, staging, production
APP_NAME=ValueVerse                     # Application name
APP_URL=http://localhost:3000           # Frontend URL
API_URL=http://localhost:8000           # API Gateway URL

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/valueverse
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-secret-key-min-32-chars  # Change in production!
SESSION_SECRET=session-secret-key        # Change in production!

# External Services (Optional)
STRIPE_SECRET_KEY=sk_test_...           # For billing
OPENAI_API_KEY=sk-...                   # For AI features
SMTP_HOST=smtp.gmail.com                # For emails
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### Service-Specific Variables

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_...
```

#### Microservices
```bash
# Each service has its own configuration
SERVICE_PORT=8011
LOG_LEVEL=info
ENABLE_TRACING=true
JAEGER_ENDPOINT=http://localhost:14268/api/traces
```

## 📚 Service Documentation

### Core Services

#### 1. Value Architect Service (Port 8011)
- **Purpose**: AI-powered value hypothesis generation
- **Endpoints**: 
  - `POST /api/v1/value-models` - Create value model
  - `GET /api/v1/value-models/{id}` - Get value model
- **Dependencies**: PostgreSQL, Redis

#### 2. Value Committer Service (Port 8012)
- **Purpose**: Commitment and contract management
- **Endpoints**:
  - `POST /api/v1/commitments` - Create commitment
  - `PUT /api/v1/commitments/{id}/milestones` - Update milestones
- **Dependencies**: PostgreSQL

#### 3. Value Executor Service (Port 8013)
- **Purpose**: Execution tracking and delivery
- **Endpoints**:
  - `POST /api/v1/executions` - Track execution
  - `GET /api/v1/executions/{id}/progress` - Get progress
- **Dependencies**: PostgreSQL, RabbitMQ

#### 4. Value Amplifier Service (Port 8014)
- **Purpose**: Success amplification and referrals
- **Endpoints**:
  - `POST /api/v1/amplifications` - Create success story
  - `GET /api/v1/amplifications/metrics` - Get metrics
- **Dependencies**: PostgreSQL

### Infrastructure Services

#### Kong API Gateway (8000/8001)
- **Admin API**: http://localhost:8001
- **Proxy**: http://localhost:8000
- **Configuration**: Automatic service discovery via Consul

#### Consul (8500)
- **UI**: http://localhost:8500
- **Purpose**: Service discovery and health checking

#### Jaeger (16686)
- **UI**: http://localhost:16686
- **Purpose**: Distributed tracing

#### Grafana (3001)
- **UI**: http://localhost:3001
- **Login**: admin/admin
- **Dashboards**: Pre-configured for all services

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use
```bash
# Error: bind: address already in use
# Solution: Find and stop the conflicting process
lsof -i :3000  # Find process using port 3000
kill -9 <PID>  # Kill the process
```

#### 2. Docker Daemon Not Running
```bash
# Error: Cannot connect to Docker daemon
# Solution: Start Docker
sudo systemctl start docker  # Linux
open -a Docker              # macOS
```

#### 3. Out of Memory
```bash
# Error: Container killed due to OOM
# Solution: Increase Docker memory
# Docker Desktop > Settings > Resources > Memory: 8GB+
```

#### 4. Database Connection Failed
```bash
# Error: ECONNREFUSED 127.0.0.1:5432
# Solution: Ensure PostgreSQL container is running
docker ps | grep postgres
docker compose -f docker-compose.infrastructure.yml up -d postgres
```

#### 5. Frontend Build Errors
```bash
# Error: Module not found
# Solution: Rebuild frontend
docker compose -f docker-compose.frontend.yml down
docker compose -f docker-compose.frontend.yml build --no-cache
docker compose -f docker-compose.frontend.yml up -d
```

### Debug Commands

```bash
# View logs for specific service
docker logs -f valueverse-value-architect

# Enter container shell
docker exec -it valueverse-postgres bash

# Check service health
curl http://localhost:8011/health

# View all running containers
docker ps

# Clean everything and restart
./scripts/clean-all.sh
./deploy.sh
```

## 💻 Development Guide

### Local Development Setup

```bash
# Enable hot-reloading
export ENABLE_HOT_RELOAD=true
./deploy.sh dev

# Or manually for specific services
cd frontend && npm run dev
cd services/value-architect && uvicorn main:app --reload
```

### Adding New Services

1. Create service directory: `services/new-service/`
2. Add Dockerfile
3. Update `docker-compose.services.yml`
4. Register in Consul
5. Add Kong route
6. Update documentation

### Testing

```bash
# Run all tests
make test

# Unit tests
make test-unit

# Integration tests
make test-integration

# E2E tests
make test-e2e
```

## 🚢 Production Deployment

### Prerequisites for Production

1. **SSL Certificates**: Required for HTTPS
2. **Domain Names**: Configure DNS
3. **Secrets Management**: Use external secret store
4. **Monitoring**: Set up alerts
5. **Backups**: Configure automated backups

### Production Configuration

```bash
# Use production compose file
docker compose -f docker-compose.prod.yml up -d

# Environment variables for production
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/valueverse
ENABLE_HTTPS=true
SSL_CERT_PATH=/etc/ssl/certs/
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n valueverse
```

## 💾 Backup & Restore

### Backup Procedures

```bash
# Full backup
./scripts/backup.sh full

# Database only
./scripts/backup.sh database

# Application state
./scripts/backup.sh state

# Scheduled backups (cron)
0 2 * * * /path/to/scripts/backup.sh full
```

### Restore Procedures

```bash
# Restore from backup
./scripts/restore.sh /path/to/backup.tar.gz

# Restore database only
./scripts/restore.sh --database-only backup.sql

# Point-in-time recovery
./scripts/restore.sh --timestamp "2024-01-15 10:00:00"
```

## 📊 Monitoring & Logging

### Available Dashboards

- **Grafana**: http://localhost:3001
  - Service Health Dashboard
  - Performance Metrics
  - Business KPIs
  - Alert Manager

- **Jaeger**: http://localhost:16686
  - Request tracing
  - Latency analysis
  - Dependency graph

### Log Aggregation

```bash
# View all logs
docker compose logs -f

# Filter by service
docker compose logs -f value-architect

# Export logs
docker compose logs > logs.txt
```

## 🔐 Security Considerations

### Default Credentials (Change in Production!)

| Service | Username | Password |
|---------|----------|----------|
| Grafana | admin | admin |
| PostgreSQL | postgres | postgres |
| RabbitMQ | admin | admin |
| Application | admin@valueverse.ai | admin123 |

### Security Checklist

- [ ] Change all default passwords
- [ ] Enable firewall rules
- [ ] Configure SSL/TLS
- [ ] Enable audit logging
- [ ] Set up intrusion detection
- [ ] Regular security updates
- [ ] Implement rate limiting
- [ ] Enable CORS properly

## 🤝 Support & Contributing

### Getting Help

- **Documentation**: This README
- **Issues**: GitHub Issues
- **Community**: Discord/Slack
- **Email**: support@valueverse.ai

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## 📄 License

Copyright © 2024 ValueVerse. All rights reserved.

---

## 🎉 Success Verification

After running `./deploy.sh`, verify your deployment:

✅ **All services healthy**: `./scripts/health-check.sh`
✅ **UI accessible**: http://localhost:3000
✅ **API responding**: http://localhost:8000/health
✅ **Monitoring active**: http://localhost:3001 (admin/admin)
✅ **Tracing working**: http://localhost:16686

**Congratulations!** Your ValueVerse platform is now fully operational! 🚀
