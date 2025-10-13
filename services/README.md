# 🚀 ValueVerse Microservices Architecture

## Overview

This directory contains the complete containerized microservices implementation of ValueVerse, transforming the monolithic backend into scalable, independent services.

## 🏗️ Architecture

```
                    ┌─────────────────┐
                    │   API Gateway   │ ←── Port 8000
                    │     (Kong)      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐      ┌──────▼──────┐     ┌──────▼──────┐
   │  Value   │      │    Value    │     │    Value    │
   │Architect │      │  Committer  │     │  Executor   │
   │  :8001   │      │    :8002    │     │    :8003    │
   └──────────┘      └─────────────┘     └─────────────┘
                             │
                    ┌────────▼────────┐
                    │     Value       │
                    │   Amplifier     │
                    │      :8004      │
                    └─────────────────┘
                    
   ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
   │ Calculation │  │Notification │  │   Shared     │
   │   Engine    │  │   Service   │  │  Services    │
   │    :8005    │  │    :8006    │  │ Redis/PG/MQ  │
   └─────────────┘  └─────────────┘  └──────────────┘
```

## 📦 Services

### Core Business Services

| Service | Port | Description | Status |
|---------|------|-------------|---------|
| **value-architect** | 8001 | Value model design & hypothesis generation | ✅ Complete |
| **value-committer** | 8002 | Commitments, contracts & deal structuring | ✅ Complete |
| **value-executor** | 8003 | Delivery tracking & milestone management | 🔨 Placeholder |
| **value-amplifier** | 8004 | Success metrics & amplification strategies | 🔨 Placeholder |
| **calculation-engine** | 8005 | Compute-intensive calculations (scales independently) | 🔨 Placeholder |
| **notification-service** | 8006 | Email/SMS/Webhook notifications | 🔨 Placeholder |

### Infrastructure Services

| Service | Port | Purpose |
|---------|------|---------|
| **Kong API Gateway** | 8000 | Single entry point, routing, rate limiting |
| **PostgreSQL** | 5432 | Primary database |
| **Redis** | 6379 | Cache & pub/sub |
| **RabbitMQ** | 5672/15672 | Message broker |
| **Consul** | 8500 | Service discovery |
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3001 | Metrics visualization |
| **Jaeger** | 16686 | Distributed tracing |

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 10GB disk space

### Deploy All Services

```bash
# 1. Build all microservice images
./deploy-microservices.sh build

# 2. Start all services
./deploy-microservices.sh start

# 3. Check health
./deploy-microservices.sh health

# 4. View logs
./deploy-microservices.sh logs
```

## 📊 Management Commands

```bash
# View all available commands
./deploy-microservices.sh help

# Stop all services
./deploy-microservices.sh stop

# Restart services
./deploy-microservices.sh restart

# Scale a service
./deploy-microservices.sh scale calculation-engine 5

# View logs for specific service
./deploy-microservices.sh logs value-architect

# Run basic tests
./deploy-microservices.sh test

# Show all service URLs
./deploy-microservices.sh urls
```

## 🌐 Service Endpoints

### API Gateway
- **Main Gateway**: http://localhost:8000
- **Admin API**: http://localhost:8001

### Direct Service Access (for debugging)
- **Value Architect**: http://localhost:8011
- **Value Committer**: http://localhost:8012
- **Value Executor**: http://localhost:8013
- **Value Amplifier**: http://localhost:8014
- **Calculation Engine**: http://localhost:8015
- **Notifications**: http://localhost:8016

### Monitoring & Management
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger UI**: http://localhost:16686
- **Consul UI**: http://localhost:8500
- **RabbitMQ Management**: http://localhost:15672 (admin/admin)

## 🔧 Development

### Adding a New Service

1. Create service directory:
```bash
mkdir services/new-service
```

2. Add main.py with FastAPI app:
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

3. Add Dockerfile and requirements.txt

4. Update docker-compose.microservices.yml

### Testing a Single Service

```bash
# Build specific service
docker-compose -f docker-compose.microservices.yml build value-architect

# Run specific service
docker-compose -f docker-compose.microservices.yml up value-architect

# Test endpoint
curl http://localhost:8011/health
```

## 📈 Scaling Strategy

### Horizontal Scaling
```yaml
# In docker-compose.microservices.yml
deploy:
  replicas: 3  # Set number of instances
```

Or dynamically:
```bash
./deploy-microservices.sh scale value-architect 5
```

### Service-Specific Scaling Recommendations

| Service | Scaling Strategy | Replicas |
|---------|-----------------|----------|
| value-architect | CPU-based | 2-4 |
| value-committer | Request-based | 2-3 |
| value-executor | Event-based | 2-5 |
| value-amplifier | CPU-based | 1-3 |
| calculation-engine | CPU-intensive | 3-10 |
| notification-service | Queue-based | 2-5 |

## 🔐 Security

- All services run as non-root users
- Health checks on all services
- Network isolation via Docker networks
- Secrets managed via environment variables
- API Gateway handles authentication/authorization

## 📊 Monitoring

### Prometheus Metrics
All services expose metrics at `/api/v1/metrics`:
- Request count
- Response times
- Error rates
- Custom business metrics

### Grafana Dashboards
Access at http://localhost:3001:
- Service health overview
- Request/response metrics
- Database performance
- Cache hit rates

### Distributed Tracing
Jaeger UI at http://localhost:16686:
- Request flow visualization
- Latency analysis
- Error tracking

## 🐛 Troubleshooting

### Service won't start
```bash
# Check logs
./deploy-microservices.sh logs <service-name>

# Check health
curl http://localhost:<port>/health

# Restart service
docker-compose -f docker-compose.microservices.yml restart <service-name>
```

### Database connection issues
```bash
# Check PostgreSQL
docker-compose -f docker-compose.microservices.yml logs postgres

# Check Redis
docker-compose -f docker-compose.microservices.yml logs redis
```

### Reset everything
```bash
# Stop and remove all containers, volumes
docker-compose -f docker-compose.microservices.yml down -v

# Rebuild and start fresh
./deploy-microservices.sh build
./deploy-microservices.sh start
```

## 🚦 Production Deployment

### Kubernetes Deployment
Each service has been designed to be Kubernetes-ready:
```bash
# Build and push images
docker build -t valueverse/value-architect:latest ./value-architect
docker push valueverse/value-architect:latest

# Deploy to Kubernetes
kubectl apply -f k8s/value-architect-deployment.yaml
```

### Environment Variables
Create `.env` file:
```env
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis:6379
KAFKA_BROKER=kafka:9092
JWT_SECRET=your-secret-key
```

## 📚 API Documentation

Each service provides OpenAPI documentation:
- Value Architect: http://localhost:8011/docs
- Value Committer: http://localhost:8012/docs
- Value Executor: http://localhost:8013/docs
- Value Amplifier: http://localhost:8014/docs

## 🎯 Benefits Achieved

✅ **Independent Scaling**: Each service scales based on its needs  
✅ **Fault Isolation**: One service failure doesn't affect others  
✅ **Technology Flexibility**: Can use different tech per service  
✅ **Team Autonomy**: Teams can work independently  
✅ **Faster Deployments**: Deploy services independently  
✅ **Better Resource Utilization**: Right-size each service  

## 📝 Next Steps

1. **Implement remaining services** (executor, amplifier, etc.)
2. **Add Kafka** for robust event streaming
3. **Implement service mesh** (Istio) for advanced traffic management
4. **Add CI/CD pipelines** for automated deployment
5. **Implement SAGA pattern** for distributed transactions
6. **Add circuit breakers** for resilience

---

**Built with ❤️ for ValueVerse Platform**
