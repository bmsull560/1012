# ValueVerse Deployment Guide

## 🚀 Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- PostgreSQL 15 (or use Docker)

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/bmsull560/1012.git
cd 1012

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your settings

# 3. Start all services
docker-compose up -d

# 4. Run migrations
docker-compose exec backend alembic upgrade head

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb valueverse

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/valueverse"
export SECRET_KEY="your-secret-key-here"

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start development server
npm run dev
```

---

## 📦 Production Deployment

### Deploy to VPS/Cloud Server

#### 1. Server Requirements
- Ubuntu 22.04 LTS (or similar)
- 2GB+ RAM
- 20GB+ storage
- Docker & Docker Compose installed

#### 2. Deploy Script

```bash
# On your server
git clone https://github.com/bmsull560/1012.git
cd 1012

# Set up production environment
cp .env.example .env.production
nano .env.production  # Configure production settings

# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Set up SSL with Let's Encrypt
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### 3. Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔐 Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/valueverse

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# API
API_V1_PREFIX=/api/v1
PROJECT_NAME=ValueVerse
DEBUG=False

# Redis (for caching/celery)
REDIS_URL=redis://redis:6379/0

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=https://yourdomain.com/api/v1
NEXT_PUBLIC_APP_NAME=ValueVerse
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm run test
npm run test:coverage
```

### E2E Tests

```bash
npm run test:e2e
```

---

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000/api/health
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U user valueverse > backup.sql

# Restore
docker-compose exec -T postgres psql -U user valueverse < backup.sql
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head
```

---

## 🔧 Troubleshooting

### Backend not starting
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Database connection: Check DATABASE_URL
# - Port conflict: Change port in docker-compose.yml
# - Migrations: Run alembic upgrade head
```

### Frontend not connecting to backend
```bash
# Check NEXT_PUBLIC_API_URL in .env.local
# Verify CORS settings in backend/app/main.py
# Check network connectivity
curl http://localhost:8000/api/v1/health
```

### Database issues
```bash
# Reset database (CAUTION: Data loss!)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend alembic upgrade head
```

---

## 🚀 CI/CD with GitHub Actions

The repository includes automated CI/CD workflows:

- **On Pull Request**: Run tests, lint, type check
- **On Push to Main**: Build Docker images, run tests
- **On Tag**: Deploy to production

### Manual Deployment Trigger

```bash
# Create a new release tag
git tag v1.0.0
git push origin v1.0.0

# This triggers the deployment workflow
```

---

## 📈 Performance Optimization

### Backend
- Enable Redis caching
- Use connection pooling
- Optimize database queries
- Enable Gzip compression

### Frontend
- Enable Next.js image optimization
- Use CDN for static assets
- Implement code splitting
- Enable service worker

### Database
- Create indexes on frequently queried columns
- Use database query optimization
- Regular VACUUM and ANALYZE
- Connection pooling

---

## 🔒 Security Checklist

- [ ] Change all default secrets and passwords
- [ ] Enable HTTPS (SSL certificate)
- [ ] Configure firewall (UFW)
- [ ] Set up fail2ban
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] Environment variables secured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] SQL injection prevention (using ORM)

---

## 📞 Support

For issues or questions:
- Create an issue: https://github.com/bmsull560/1012/issues
- Check documentation: https://github.com/bmsull560/1012/wiki

---

## 🎯 What's Built

✅ **Backend (FastAPI)**
- User authentication with JWT
- Organization management
- Value driver tracking
- RESTful API
- Database migrations
- Comprehensive tests

✅ **Frontend (Next.js)**
- Authentication flow
- Dashboard
- Organizations management
- Responsive design
- Type-safe with TypeScript

✅ **Infrastructure**
- Docker Compose setup
- Nginx reverse proxy
- PostgreSQL database
- Redis caching
- Automated deployments

**Built entirely by the Agentic AI Development System! 🤖**
