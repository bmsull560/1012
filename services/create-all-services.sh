#!/bin/bash

# Script to create all microservices
echo "🚀 Creating ValueVerse Microservices Architecture"

# Create placeholder services
for service in value-executor value-amplifier calculation-engine notification-service; do
    echo "Creating $service..."
    
    # Create main.py
    cat > services/$service/main.py << 'EOF'
from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()
SERVICE_NAME = os.path.basename(os.getcwd())
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))

@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def ready():
    return {"status": "ready"}

@app.get("/api/v1/metrics")
async def metrics():
    return {"service": SERVICE_NAME, "uptime": "99.9%"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
EOF
    
    # Create requirements.txt
    cat > services/$service/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
redis==5.0.1
httpx==0.25.1
EOF
    
    # Create Dockerfile
    cat > services/$service/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
    
    echo "✅ Created $service"
done

# Create monitoring configuration
mkdir -p services/monitoring

# Prometheus config
cat > services/monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'value-architect'
    static_configs:
      - targets: ['value-architect:8001']
  
  - job_name: 'value-committer'
    static_configs:
      - targets: ['value-committer:8002']
  
  - job_name: 'value-executor'
    static_configs:
      - targets: ['value-executor:8003']
  
  - job_name: 'value-amplifier'
    static_configs:
      - targets: ['value-amplifier:8004']
  
  - job_name: 'calculation-engine'
    static_configs:
      - targets: ['calculation-engine:8005']
  
  - job_name: 'notification-service'
    static_configs:
      - targets: ['notification-service:8006']
EOF

# Grafana datasource
cat > services/monitoring/grafana-datasources.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

echo ""
echo "✅ All microservices created successfully!"
echo ""
echo "📦 Services created:"
echo "  - value-architect (port 8001)"
echo "  - value-committer (port 8002)"
echo "  - value-executor (port 8003)"
echo "  - value-amplifier (port 8004)"
echo "  - calculation-engine (port 8005)"
echo "  - notification-service (port 8006)"
echo ""
echo "🚀 To start all microservices:"
echo "  cd services"
echo "  docker-compose -f docker-compose.microservices.yml up --build"
echo ""
echo "🌐 Access points:"
echo "  - API Gateway: http://localhost:8000"
echo "  - Kong Admin: http://localhost:8001"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Jaeger UI: http://localhost:16686"
echo "  - Consul UI: http://localhost:8500"
echo "  - RabbitMQ: http://localhost:15672 (admin/admin)"
