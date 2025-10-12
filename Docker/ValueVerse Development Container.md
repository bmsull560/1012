# ValueVerse Development Container

## Overview

This development container provides a complete, production-like environment for developing the ValueVerse platform. It includes all necessary tools, extensions, and services to enable seamless full-stack development.

## What's Included

### Core Services

The development environment consists of multiple interconnected services orchestrated through Docker Compose:

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| **app** | Node.js 22 + Python 3.11 | - | Main development container with all tools |
| **db** | TimescaleDB (PostgreSQL 15) | 5432 | Time-series optimized database |
| **redis** | Redis 7 | 6379 | Caching and session management |

### Development Tools

The container comes pre-configured with a comprehensive suite of development tools:

**Python Ecosystem:**
- Python 3.11 with pip and venv
- Black (code formatter)
- isort (import organizer)
- Flake8 (linter)
- mypy (type checker)
- pytest (testing framework)

**Node.js Ecosystem:**
- Node.js 22 with npm, pnpm, and yarn
- TypeScript and ts-node
- ESLint and Prettier
- Global type definitions

**Database Tools:**
- PostgreSQL client (psql)
- Redis CLI (redis-cli)

**System Utilities:**
- Git with GitHub CLI
- Docker-in-Docker support
- vim, nano, less
- jq (JSON processor)
- htop (process monitor)

### VS Code Extensions

The container automatically installs and configures 30+ essential VS Code extensions, including:

- **Python Development:** Python, Pylance, Black, isort, Flake8, Ruff
- **JavaScript/TypeScript:** ESLint, Prettier, Tailwind CSS IntelliSense
- **Database:** SQLTools with PostgreSQL driver
- **Testing:** Test Explorer, Playwright
- **AI Assistance:** GitHub Copilot and Copilot Chat
- **Code Quality:** SonarLint, Error Lens
- **Git:** GitLens, Git Graph
- **Documentation:** Markdown All in One, Mermaid diagrams

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed on your host machine:

1. **Visual Studio Code** (latest version)
2. **Docker Desktop** (or Docker Engine + Docker Compose)
3. **Dev Containers Extension** for VS Code

### Opening the Project

There are two methods to open the project in the dev container:

**Method 1: Command Palette**
1. Open VS Code
2. Press `F1` or `Ctrl+Shift+P` (Windows/Linux) / `Cmd+Shift+P` (Mac)
3. Type "Dev Containers: Open Folder in Container"
4. Select the ValueVerse project folder

**Method 2: Notification Prompt**
1. Open the ValueVerse project folder in VS Code
2. When prompted, click "Reopen in Container"

The first build will take several minutes as it downloads and configures all dependencies. Subsequent starts will be much faster.

### Post-Creation Setup

After the container is built and started, the `post-create.sh` script automatically:

- Installs Python dependencies from `requirements.txt`
- Installs Node.js dependencies from `package.json`
- Sets up pre-commit hooks if configured
- Initializes the database schema
- Creates necessary directories (logs, data, uploads)

## Working in the Container

### Running the Application

**Frontend (Next.js):**
```bash
cd frontend
npm run dev
# Access at http://localhost:3000
```

**Backend (FastAPI):**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Access at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Database Access

**Connect to PostgreSQL:**
```bash
psql -h db -U user -d valuedb
# Password: password
```

**Connect to Redis:**
```bash
redis-cli -h redis
```

### Running Tests

**Python Tests:**
```bash
pytest
pytest --cov=. --cov-report=html
```

**Frontend Tests:**
```bash
cd frontend
npm test
npm run test:e2e
```

### Code Quality Checks

**Python:**
```bash
black .
isort .
flake8 .
mypy .
```

**TypeScript:**
```bash
npm run lint
npm run format
```

## Configuration Details

### Environment Variables

The following environment variables are automatically configured:

- `DATABASE_URL`: Connection string for PostgreSQL
- `REDIS_URL`: Connection string for Redis
- `NODE_ENV`: Set to "development"
- `PYTHONUNBUFFERED`: Ensures Python output is not buffered

You can add custom environment variables in the `docker-compose.yml` file under the `app` service.

### Port Forwarding

The following ports are automatically forwarded from the container to your host:

- **3000**: Frontend (Next.js) - Auto-notifies when ready
- **8000**: Backend (FastAPI) - Auto-notifies when ready
- **5432**: PostgreSQL - Silent forwarding
- **6379**: Redis - Silent forwarding

### VS Code Settings

The container applies optimized settings for the ValueVerse tech stack:

- **Format on Save** enabled for all file types
- **Auto-organize imports** for Python and TypeScript
- **ESLint auto-fix** on save for JavaScript/TypeScript
- **Black formatter** for Python
- **Prettier formatter** for TypeScript/JavaScript/JSON
- **80/120 character rulers** for code width guidance

## Customization

### Adding VS Code Extensions

To add more extensions, edit `.devcontainer/devcontainer.json` and add the extension ID to the `extensions` array:

```json
"customizations": {
  "vscode": {
    "extensions": [
      "publisher.extension-name"
    ]
  }
}
```

### Adding System Packages

To install additional system packages, edit `.devcontainer/Dockerfile` and add them to the `apt-get install` command:

```dockerfile
RUN apt-get update && apt-get -y install --no-install-recommends \
    your-package-name \
    && apt-get clean
```

### Adding Python Packages

Add packages to `requirements.txt` in the project root, then rebuild the container or run:

```bash
pip3 install --user -r requirements.txt
```

### Adding Node.js Packages

Add packages to `package.json` or install directly:

```bash
npm install package-name
```

## Troubleshooting

### Container Won't Start

1. Ensure Docker Desktop is running
2. Check Docker has sufficient resources (4GB RAM minimum, 8GB recommended)
3. Try rebuilding: `F1` → "Dev Containers: Rebuild Container"

### Database Connection Issues

1. Verify the database service is running: `docker-compose ps`
2. Check the connection string in environment variables
3. Ensure PostgreSQL port 5432 is not in use on the host

### Extension Not Working

1. Reload the window: `F1` → "Developer: Reload Window"
2. Check the extension is installed: View → Extensions
3. Rebuild the container if the issue persists

### Performance Issues

1. Increase Docker Desktop resources (CPU and RAM)
2. Use named volumes instead of bind mounts for node_modules
3. Disable unnecessary extensions

## Best Practices

### Security

- Never commit secrets to the repository
- Use environment variables for sensitive configuration
- Keep dependencies up to date with security patches
- Run security scans regularly with `npm audit` and `pip-audit`

### Performance

- Use `.dockerignore` to exclude unnecessary files from the build context
- Leverage Docker layer caching by organizing Dockerfile commands efficiently
- Use multi-stage builds for production images

### Collaboration

- Document any custom setup steps in this README
- Share common tasks as npm/make scripts
- Use pre-commit hooks to enforce code quality standards
- Keep the dev container configuration in version control

## Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

## Support

For issues or questions about the development environment:

1. Check this README for common solutions
2. Review the [ValueVerse coding guidelines](../coding_rules_final.md)
3. Consult the team's internal documentation
4. Reach out to the DevOps team

---

**Happy coding! 🚀**

