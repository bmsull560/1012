# Docker Configuration Files

This directory contains the source configuration files for the ValueVerse development container.

## ℹ️ Important Note

The **active dev container configuration** is located in `/.devcontainer/` directory at the project root.

This `Docker/` directory serves as:
- Documentation and reference for the dev container setup
- Source of truth for container configuration
- Archive of container-related documentation

## 📁 Files in This Directory

| File | Purpose | Status |
|------|---------|--------|
| `devcontainer.json` | VS Code dev container config | Reference copy |
| `docker-compose.yml` | Service orchestration | Reference copy |
| `Dockerfile` | Container image definition | Reference copy |
| `post-create.sh` | Post-creation setup script | Reference copy |
| `dockerignore` | Docker ignore patterns | Reference copy |
| `env.example` | Environment variables template | Reference copy |
| `ValueVerse Development Container.md` | Comprehensive documentation | Active |
| `ValueVerse Dev Container - Quick Start Guide.md` | Quick start guide | Active |

## 🚀 Getting Started

**To use the dev container, refer to:**
- [`/.devcontainer/README.md`](../.devcontainer/README.md) - Active configuration documentation
- [`ValueVerse Dev Container - Quick Start Guide.md`](./ValueVerse%20Dev%20Container%20-%20Quick%20Start%20Guide.md) - Quick start

## 📖 Documentation

### Quick Start Guide
[`ValueVerse Dev Container - Quick Start Guide.md`](./ValueVerse%20Dev%20Container%20-%20Quick%20Start%20Guide.md)

5-minute setup guide with:
- Prerequisites checklist
- Step-by-step setup
- Common commands
- Troubleshooting

### Comprehensive Guide
[`ValueVerse Development Container.md`](./ValueVerse%20Development%20Container.md)

Complete documentation including:
- Full architecture overview
- All included tools and extensions
- Configuration details
- Best practices
- Advanced customization

## 🔄 Syncing Changes

When making changes to dev container configuration:

1. **Edit files in** `/.devcontainer/`
2. **Rebuild container**: `F1` → "Dev Containers: Rebuild Container"
3. **Update reference copies** in this directory if needed
4. **Update documentation** to reflect changes

## 🏗️ Container Architecture

```
Dev Container
├── Services
│   ├── app (Python 3.11 + Node.js 22)
│   ├── db (TimescaleDB/PostgreSQL 15)
│   └── redis (Redis 7)
│
├── Tools
│   ├── Python (FastAPI, LangChain, pytest)
│   ├── Node.js (TypeScript, ESLint, Prettier)
│   └── Database (psql, redis-cli)
│
└── VS Code Extensions (30+)
    ├── Python Development
    ├── JavaScript/TypeScript
    ├── Database Tools
    └── Git, Docker, Testing
```

## 🔧 Configuration Overview

### Services Configuration (docker-compose.yml)

- **app**: Main dev container with all tools
- **db**: TimescaleDB on port 5432
- **redis**: Redis on port 6379

### Container Image (Dockerfile)

Based on: `mcr.microsoft.com/devcontainers/base:ubuntu-22.04`

Includes:
- Python 3.11 ecosystem
- Node.js 22 ecosystem
- PostgreSQL and Redis clients
- Docker CLI
- GitHub CLI
- Development utilities

### Post-Creation Script (post-create.sh)

Automatically runs after container creation:
- Installs Python dependencies from `requirements.txt`
- Installs Node.js dependencies from `package.json`
- Sets up pre-commit hooks
- Initializes database schema
- Creates necessary directories

## 📝 Environment Variables

Template available at: [`env.example`](./env.example)

Copy to project root as `.env`:
```bash
cp Docker/env.example .env
```

## 🐛 Troubleshooting

See:
- [`/.devcontainer/README.md`](../.devcontainer/README.md#-troubleshooting)
- [`ValueVerse Development Container.md`](./ValueVerse%20Development%20Container.md#troubleshooting)

## 🔗 Related Documentation

- **Project README**: [`/README.md`](../README.md)
- **Active Dev Container**: [`/.devcontainer/`](../.devcontainer/)
- **Contributing Guide**: [`/CONTRIBUTING.md`](../CONTRIBUTING.md)
- **Project Status**: [`/PROJECT_STATUS.md`](../PROJECT_STATUS.md)

## 📚 External Resources

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Docker Compose](https://docs.docker.com/compose/)
- [TimescaleDB](https://docs.timescale.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)

---

**Status**: ✅ Dev container fully configured and operational
