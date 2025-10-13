# ValueVerse Development Container

This directory contains the VS Code Dev Container configuration for the ValueVerse platform.

## 🚀 Quick Start

### Prerequisites

- **Visual Studio Code** (latest version)
- **Docker Desktop** (8GB RAM recommended)
- **Dev Containers extension** for VS Code ([Install](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers))

### Getting Started

1. **Open the project in VS Code**:

```bash
code /path/to/1012
```

2. **Reopen in Container**:

   - Click the notification that appears, OR
   - Press `F1` → "Dev Containers: Reopen in Container"

3. **Wait for the build** (first time: 3-5 minutes)

4. **Verify the setup**:

```bash
# Check Python
python --version  # Should be 3.11+

# Check Node.js
node --version    # Should be 22.x

# Check database
psql -h localhost -U user -d valuedb -c "SELECT version();"
# Password: password
```

## 📁 Configuration Files

| File                 | Purpose                                |
| -------------------- | -------------------------------------- |
| `devcontainer.json`  | VS Code Dev Container configuration    |
| `docker-compose.yml` | Service orchestration (app, db, redis) |
| `Dockerfile`         | Container image definition             |
| `post-create.sh`     | Post-creation setup script             |

## 🏗️ Architecture

### Services

The dev container runs three services:

1. **app** - Main development container with Python + Node.js
2. **db** - TimescaleDB (PostgreSQL 15 with time-series extension)
3. **redis** - Redis 7 for caching

### Network Configuration

Services communicate using Docker's internal networking:

- PostgreSQL: `localhost:5432` (forwarded to host)
- Redis: `localhost:6379` (forwarded to host)

### Volumes

- **postgres-data**: Persistent PostgreSQL database
- **redis-data**: Persistent Redis data
- **node_modules**: Cached Node.js dependencies
- **venv**: Cached Python virtual environment

## 🛠️ Development Tools Included

### Python Tools

- Python 3.11 with pip and venv
- **Formatters**: black, isort
- **Linters**: flake8, pylint, ruff
- **Type Checking**: mypy
- **Testing**: pytest, pytest-cov
- **Frameworks**: FastAPI, LangChain, SQLAlchemy

### Node.js Tools

- Node.js 22 with npm, pnpm, yarn
- **TypeScript**: typescript, ts-node
- **Linters**: ESLint
- **Formatters**: Prettier

### Database Tools

- PostgreSQL client (psql)
- Redis CLI (redis-cli)
- Alembic (database migrations)

### System Utilities

- Git + GitHub CLI
- Docker CLI (for Docker-in-Docker)
- vim, nano, jq, htop

### VS Code Extensions (30+)

Pre-installed extensions include:

- Python, Pylance, Black, isort, Flake8, Ruff
- ESLint, Prettier, Tailwind CSS IntelliSense
- SQLTools with PostgreSQL driver
- GitHub Copilot (if licensed)
- GitLens, Git Graph
- Docker, Kubernetes Tools
- Markdown All in One

## 🔧 Customization

### Adding VS Code Extensions

Edit `devcontainer.json`:

```json
"customizations": {
  "vscode": {
    "extensions": [
      "publisher.extension-id"
    ]
  }
}
```

### Adding System Packages

Edit `Dockerfile`:

```dockerfile
RUN apt-get update && apt-get install -y \
    your-package-name \
    && apt-get clean
```

### Adding Python Packages

Create/edit `requirements.txt` in project root:

```
fastapi>=0.104.0
sqlalchemy>=2.0.0
```

Then rebuild the container.

### Adding Node.js Packages

Create/edit `package.json` in project root or run:

```bash
npm install package-name
```

## 🐛 Troubleshooting

### Container Won't Start

**Issue**: Docker is not running
**Solution**: Start Docker Desktop and wait for it to fully initialize

**Issue**: Port conflicts
**Solution**: Check if ports 5432, 6379, 3000, or 8000 are in use:

```bash
lsof -i :5432
lsof -i :6379
```

### Database Connection Issues

**Check database is running**:

```bash
docker ps | grep timescale
```

**Restart database**:

```bash
docker-compose restart db
```

**Reset database**:

```bash
docker-compose down -v
docker-compose up -d
```

### Extension Not Working

**Reload window**:

```
F1 → "Developer: Reload Window"
```

**Rebuild container**:

```
F1 → "Dev Containers: Rebuild Container"
```

### Performance Issues

**Increase Docker resources**:

- Open Docker Desktop → Settings → Resources
- Increase CPU cores and RAM (recommend 8GB)

**Clear cache**:

```bash
docker system prune -a
```

## 📝 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` - OpenAI API key (for AI features)
- `ANTHROPIC_API_KEY` - Anthropic API key
- `JWT_SECRET_KEY` - Secret for JWT tokens

**⚠️ Never commit `.env` to version control!**

## 🧪 Running Tests

```bash
# Backend tests
cd backend
pytest
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
npm run test:e2e
```

## 🏃 Running the Application

### Backend (FastAPI)

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access at:

- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### Frontend (Next.js)

```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000

## 🔒 Security Notes

- Database credentials in `docker-compose.yml` are for **development only**
- Change all default passwords in production
- Never expose development ports publicly
- Use environment variables for all secrets
- Keep Docker and dependencies updated

## 📚 Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Project Documentation](../docs/README.md)

## 💡 Tips

- Use **Ctrl+`** to open integrated terminal
- Run `docker-compose logs -f db` to monitor database logs
- Use **Ctrl+Shift+P** to access VS Code command palette
- SSH keys are mounted from host (`~/.ssh`) for git operations

---

For detailed development guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md)
