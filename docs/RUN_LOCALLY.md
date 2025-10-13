# 🚀 Running VROS Locally

## ✅ **Your SaaS App is LIVE!**

All services are running and ready to use:

```
✅ Frontend:  http://localhost:3000 (Up & Running)
✅ Backend:   http://localhost:8000 (Up & Running)  
✅ Database:  localhost:5432 (Healthy)
```

---

## 🌐 **Access Your Application**

### **1. Main Dashboard**
🔗 **http://localhost:3000**

Welcome page showing:
- System status
- Component overview
- Quick links

### **2. AI Chat Interface**
🔗 **http://localhost:3000/chat**

Interactive chat component featuring:
- User/assistant message display
- Loading animations
- Real-time messaging
- Modern UI with Tailwind CSS

### **3. API Documentation**
🔗 **http://localhost:8000/docs**

**Interactive Swagger UI** with:
- Try all API endpoints
- See request/response schemas
- Test authentication
- View all 13+ endpoints

### **4. Alternative API Docs**
🔗 **http://localhost:8000/redoc**

ReDoc documentation (cleaner, read-only format)

---

## 🧪 **Test the API**

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health
# Response: {"status":"healthy"}

# API v1 health
curl http://localhost:8000/api/v1/health
# Response: {"status":"healthy","api_version":"v1"}
```

### Graph Node API

```bash
# List all graph nodes (empty initially)
curl http://localhost:8000/api/v1/graph/nodes

# Create a test hypothesis node
curl -X POST http://localhost:8000/api/v1/graph/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "hypothesis",
    "phase": 0,
    "properties": {
      "title": "Reduce support costs",
      "description": "AI automation can reduce costs by 30%"
    },
    "confidence_score": 0.75
  }'

# Get specific node (replace {id} with actual UUID)
curl http://localhost:8000/api/v1/graph/nodes/{id}

# Update node phase to commitment
curl -X PATCH http://localhost:8000/api/v1/graph/nodes/{id} \
  -H "Content-Type: application/json" \
  -d '{"phase": 1, "confidence_score": 0.85}'
```

### AI Agent API

```bash
# Chat with Value Architect
curl -X POST http://localhost:8000/api/v1/agents/architect/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Our customer support costs are increasing rapidly"
  }'

# Extract pain points from conversation
curl -X POST http://localhost:8000/api/v1/agents/architect/discover \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": "We have 50 support agents handling 10,000 tickets per month. Response time is 24 hours."
  }'

# Generate value hypothesis
curl -X POST http://localhost:8000/api/v1/agents/architect/hypothesis \
  -H "Content-Type: application/json" \
  -d '{
    "pain_points": ["High support costs", "Slow response times"],
    "product_features": ["AI-powered ticket routing", "Automated responses"]
  }'
```

### Salesforce Integration

```bash
# Check Salesforce connection (requires credentials)
curl http://localhost:8000/api/v1/integrations/salesforce/health

# List opportunities (requires credentials)
curl http://localhost:8000/api/v1/integrations/salesforce/opportunities

# Filter by stage
curl "http://localhost:8000/api/v1/integrations/salesforce/opportunities?stage=Qualification"
```

### WebSocket Testing

```javascript
// Test WebSocket connection (in browser console or Node.js)
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/test-workspace');

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({ message: 'Hello from client' }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

---

## 🎮 **Docker Commands**

### View Status

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Logs for specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

### Control Services

```bash
# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes (CAUTION: deletes database data)
docker-compose down -v

# Remove everything including images
docker-compose down --rmi all -v
```

---

## ⚙️ **Configuration**

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres_password@postgres:5432/valueverse
POSTGRES_DB=valueverse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password

# AI API Keys
TOGETHER_API_KEY=your_together_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Salesforce (optional)
SALESFORCE_USERNAME=your_username@company.com
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_security_token
SALESFORCE_DOMAIN=login  # or 'test' for sandbox

# JWT Authentication
JWT_SECRET_KEY=your_super_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Apply Configuration Changes

```bash
# Restart services to pick up new environment variables
docker-compose down
docker-compose up -d
```

---

## 🔧 **Troubleshooting**

### Backend Not Starting

```bash
# Check backend logs
docker-compose logs backend

# Common issues:
# 1. Missing dependencies - rebuild:
docker-compose build backend

# 2. Database connection - check postgres:
docker-compose logs postgres

# 3. Port conflict - check if 8000 is in use:
lsof -i :8000
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Common issues:
# 1. Build errors - rebuild:
docker-compose build frontend

# 2. Port conflict - check if 3000 is in use:
lsof -i :3000

# 3. Clear cache and rebuild:
docker-compose down
docker-compose up -d --build frontend
```

### Database Issues

```bash
# Check if database is healthy
docker-compose ps postgres

# Connect to database directly
docker-compose exec postgres psql -U postgres -d valueverse

# Reset database (CAUTION: deletes all data)
docker-compose down -v
docker-compose up -d
```

### WebSocket Connection Failed

```bash
# Check backend is running
curl http://localhost:8000/health

# Test WebSocket endpoint exists
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     http://localhost:8000/api/v1/ws/test
```

---

## 📊 **Service Details**

### Backend (FastAPI)

- **Port**: 8000
- **Language**: Python 3.11
- **Framework**: FastAPI 0.85.1
- **Features**:
  - 13+ REST API endpoints
  - WebSocket support
  - AI agent integration
  - Salesforce adapter
  - PostgreSQL database
  - Auto-reload in development

### Frontend (Next.js)

- **Port**: 3000
- **Language**: TypeScript 5.2.0
- **Framework**: Next.js 14.0.0
- **Features**:
  - Server-side rendering
  - Static optimization
  - React 18.2.0
  - Tailwind CSS
  - Hot module replacement

### Database (PostgreSQL)

- **Port**: 5432
- **Version**: 15-alpine
- **Database**: valueverse
- **Features**:
  - Graph nodes table
  - Temporal tracking
  - JSON properties
  - UUID primary keys

---

## 🚀 **Production Deployment**

### Prerequisites

```bash
# Set production environment variables
export NODE_ENV=production
export PYTHONUNBUFFERED=1

# Update .env with production values
# - Use strong JWT secrets
# - Add real API keys
# - Configure production database
```

### Build for Production

```bash
# Build optimized images
docker-compose -f docker-compose.prod.yml build

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d
```

### Recommended Production Setup

1. **Reverse Proxy**: nginx or Traefik
2. **SSL/TLS**: Let's Encrypt certificates
3. **Database**: Managed PostgreSQL (AWS RDS, Azure Database)
4. **Monitoring**: Prometheus + Grafana
5. **Logging**: ELK Stack or CloudWatch
6. **Secrets**: AWS Secrets Manager or Vault

---

## 📚 **API Endpoints Summary**

### Core API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Backend health check |
| GET | `/api/v1/health` | API version health |
| GET | `/docs` | Interactive API docs |

### Graph Nodes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/graph/nodes` | Create graph node |
| GET | `/api/v1/graph/nodes` | List nodes (filter by phase/type) |
| GET | `/api/v1/graph/nodes/{id}` | Get specific node |
| PATCH | `/api/v1/graph/nodes/{id}` | Update node |

### AI Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/agents/architect/chat` | Chat with Value Architect |
| POST | `/api/v1/agents/architect/discover` | Extract pain points |
| POST | `/api/v1/agents/architect/hypothesis` | Generate hypothesis |

### Salesforce

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/integrations/salesforce/opportunities` | List opportunities |
| GET | `/api/v1/integrations/salesforce/opportunities/{id}` | Get opportunity |
| PATCH | `/api/v1/integrations/salesforce/opportunities/{id}` | Update opportunity |
| POST | `/api/v1/integrations/salesforce/opportunities/{id}/roi` | Update ROI fields |
| GET | `/api/v1/integrations/salesforce/health` | Connection health |

### WebSocket

| Protocol | Endpoint | Description |
|----------|----------|-------------|
| WS | `ws://localhost:8000/api/v1/ws/{workspace_id}` | Real-time connection |

---

## 🎯 **Next Steps**

### 1. Configure AI Integration

```bash
# Get Together.ai API key from: https://api.together.xyz
# Add to .env:
echo "TOGETHER_API_KEY=your_key_here" >> .env

# Restart backend
docker-compose restart backend
```

### 2. Test AI Chat

Open http://localhost:3000/chat and:
- Type a message about business challenges
- See the AI response (currently echo mode)
- Connect to backend AI endpoint for real responses

### 3. Create Graph Nodes

Use the API docs at http://localhost:8000/docs to:
- Create hypothesis nodes
- Progress through phases
- Query by confidence score
- Visualize value progression

### 4. Integrate Salesforce (Optional)

```bash
# Add Salesforce credentials to .env
SALESFORCE_USERNAME=your_email@company.com
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token
SALESFORCE_DOMAIN=login

# Test connection
curl http://localhost:8000/api/v1/integrations/salesforce/health
```

---

## 🏆 **You're All Set!**

Your **ValueVerse VROS SaaS Platform** is now running locally with:

✅ **Frontend UI** - Modern React interface  
✅ **Backend API** - FastAPI with 13+ endpoints  
✅ **Database** - PostgreSQL with graph nodes  
✅ **AI Agent** - Value Architect for discovery  
✅ **CRM Integration** - Salesforce adapter  
✅ **WebSocket** - Real-time communication  

**Start building value!** 🚀

---

## 📞 **Quick Reference**

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart backend
docker-compose restart backend

# Rebuild all
docker-compose up -d --build

# Health check
curl http://localhost:8000/health
```

**Main URLs**:
- Frontend: http://localhost:3000
- Chat: http://localhost:3000/chat
- API Docs: http://localhost:8000/docs
- Backend: http://localhost:8000

---

**Last Updated**: 2025-10-12  
**Status**: ✅ **FULLY OPERATIONAL**
