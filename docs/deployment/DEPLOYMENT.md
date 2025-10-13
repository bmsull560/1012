# 🚀 ValueVerse One-Command Deployment Guide

## Quick Start

Deploy the entire ValueVerse application with a single command:

```bash
make deploy
```

**That's it!** The application will be fully deployed and accessible in under 5 minutes.

---

## 📋 Prerequisites

Before running the deployment, ensure you have:

### Required
- **Docker** (version 20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (version 2.0+) - Usually included with Docker Desktop

### Optional
- **Make** - For using Makefile commands (alternative: use `./deploy.sh`)
- **curl** - For health checks (usually pre-installed)

### Verify Prerequisites

```bash
# Check Docker
docker --version
docker info

# Check Docker Compose
docker-compose --version
# OR
docker compose version
```

---

## 🎯 Deployment Methods

### Method 1: Using Makefile (Recommended for Linux/macOS)

```bash
make deploy
```

### Method 2: Using Shell Script (Cross-platform)

```bash
./deploy.sh
```

### Method 3: Using Docker Compose Directly

```bash
# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d --build

# Check status
docker-compose ps
```

---

## 📊 What Gets Deployed

The deployment command sets up:

1. **PostgreSQL Database** (Port 5432)
   - Pre-configured with ValueVerse schema
   - Persistent data volume
   - Health checks enabled

2. **FastAPI Backend** (Port 8000)
   - REST API endpoints
   - WebSocket support
   - Auto-reload in development mode
   - Interactive API docs at `/docs`

3. **Next.js Frontend** (Port 3000)
   - React-based UI
   - Server-side rendering
   - Hot module replacement

---

## ✅ Expected Output

After running `make deploy`, you should see:

```
╔════════════════════════════════════════╗
║   ValueVerse Local Deployment v1.0    ║
╚════════════════════════════════════════╝

→ Checking dependencies...
✓ All dependencies are installed

→ Setting up environment...
✓ Created .env file from template

→ Starting services...
✓ Services started

→ Waiting for services to be ready...
  ✓ Database is ready
  ✓ Backend is ready
  ✓ Frontend is ready

→ Running health checks...
  Database: ✓ Healthy
  Backend: ✓ Healthy
  Frontend: ✓ Healthy

✓ Deployment complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 Frontend: http://localhost:3000
🔌 Backend API: http://localhost:8000
📚 API Docs: http://localhost:8000/docs
🗄️  Database: localhost:5432
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔧 Useful Commands

### Service Management

```bash
# View service status
make status

# View logs (all services)
make logs

# View specific service logs
make logs-backend
make logs-frontend
make logs-db

# Restart services
make restart

# Rebuild services (after code changes)
make rebuild

# Stop services
make stop

# Clean everything (removes data!)
make clean
```

### Development Tools

```bash
# Open backend shell
make shell-backend

# Open frontend shell
make shell-frontend

# Open database shell
make shell-db

# Run tests
make test

# Check health
make health
```

---

## 🌐 Accessing the Application

Once deployed, access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main application interface |
| **Backend API** | http://localhost:8000 | REST API endpoints |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Database** | localhost:5432 | PostgreSQL (credentials in .env) |

---

## 🔒 Environment Configuration

The deployment automatically creates a `.env` file from `.env.example`. 

### Update API Keys (Optional)

Edit `.env` to add your API keys:

```bash
# Edit environment file
nano .env  # or your preferred editor
```

Important variables:
- `OPENAI_API_KEY` - For OpenAI integration
- `ANTHROPIC_API_KEY` - For Claude integration
- `TOGETHER_API_KEY` - For Together AI
- `DATABASE_URL` - Database connection (auto-configured)
- `JWT_SECRET_KEY` - Authentication secret

After updating, restart:
```bash
make restart
```

---

## 🐛 Troubleshooting

### Issue: Port Already in Use

**Symptom:** Error binding to port 3000, 8000, or 5432

**Solution:**
```bash
# Find and stop conflicting services
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5432 | xargs kill -9  # Database

# Or use different ports in docker-compose.yml
```

### Issue: Docker Not Running

**Symptom:** "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker Desktop (macOS/Windows)
# OR
sudo systemctl start docker  # Linux
```

### Issue: Services Not Healthy

**Symptom:** Health check shows "Unhealthy" or "Not responding"

**Solution:**
```bash
# Check logs for errors
make logs

# Rebuild services
make rebuild

# Check Docker resources
docker stats
```

### Issue: Frontend Build Errors

**Symptom:** Frontend container exits or shows build errors

**Solution:**
```bash
# View frontend logs
make logs-frontend

# Rebuild with no cache
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Issue: Database Connection Errors

**Symptom:** Backend can't connect to database

**Solution:**
```bash
# Check database status
make logs-db

# Restart database
docker-compose restart postgres

# Verify connection
make shell-db
```

### Issue: Permission Denied on deploy.sh

**Symptom:** "./deploy.sh: Permission denied"

**Solution:**
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 🔄 Common Workflows

### First Time Setup
```bash
# 1. Deploy
make deploy

# 2. Check everything is running
make status

# 3. Open application
open http://localhost:3000  # macOS
xdg-open http://localhost:3000  # Linux
start http://localhost:3000  # Windows
```

### Making Code Changes
```bash
# Backend changes auto-reload (no restart needed)

# Frontend changes auto-reload (no restart needed)

# For major changes, rebuild:
make rebuild
```

### Stopping Work for the Day
```bash
# Stop services (keeps data)
make stop

# Resume tomorrow
make start
```

### Starting Fresh
```bash
# Remove everything and start over
make clean
make deploy
```

---

## ⚡ Performance Tips

### Faster Builds

```bash
# Use BuildKit for faster Docker builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### Resource Allocation

Ensure Docker has sufficient resources:
- **Memory:** At least 4GB (8GB recommended)
- **CPUs:** At least 2 cores (4+ recommended)
- **Disk:** At least 10GB free space

Configure in Docker Desktop → Preferences → Resources

---

## 🔐 Security Notes

### Development vs Production

This deployment is configured for **local development**. For production:

1. Change all default passwords in `.env`
2. Use proper secrets management
3. Enable HTTPS/TLS
4. Configure firewall rules
5. Use environment-specific configurations
6. Enable authentication/authorization
7. Review and harden Docker security

---

## 📚 Additional Resources

- [ValueVerse Documentation](./docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Contributing Guide](./CONTRIBUTING.md)

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `make logs`
2. Check status: `make status`
3. Run health checks: `make health`
4. Review this troubleshooting guide
5. Check Docker resources and system requirements

For additional help:
- Review the [GitHub Issues](https://github.com/your-org/valueverse/issues)
- Check the [Contributing Guide](./CONTRIBUTING.md)

---

## 📝 Summary

| Command | Purpose | Time |
|---------|---------|------|
| `make deploy` | Complete deployment | ~3-5 min |
| `make stop` | Stop services | ~10 sec |
| `make restart` | Restart services | ~30 sec |
| `make clean` | Remove everything | ~15 sec |
| `make logs` | View logs | Instant |
| `make status` | Check status | Instant |

**Deployment is idempotent** - safe to run multiple times without issues.

---

🎉 **Enjoy building with ValueVerse!**
