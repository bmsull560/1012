# 🚀 ValueVerse Platform

> **Enterprise-Grade Value Intelligence Platform**  
> AI-powered value modeling, ROI analysis, and stakeholder engagement for SaaS companiesonships into perpetual value creation engines

## 🏗️ Repository Structure

```
valueverse/
├── services/             # FastAPI microservices (architect, committer, etc.)
├── billing-system/       # Dedicated billing service (FastAPI + Stripe)
├── frontend/             # Next.js 14 frontend (App Router)
├── infrastructure/       # Docker + Kubernetes configurations
├── scripts/              # Deployment and maintenance automation
├── docs/                 # Architecture, deployment, and dev guides
├── docker-compose.*.yml  # Compose bundles for microservices + tooling
└── requirements.txt      # Python dependency lock (see section below)
```

## ⚡ Quick Start - One Command Deployment

Deploy the entire application locally in under 5 minutes:

### Linux/macOS
```bash
make deploy
```

### Windows (PowerShell)
```powershell
.\deploy.ps1
```

### Alternative (All platforms)
```bash
./deploy.sh
```

**That's it!** After 3-5 minutes, access:
- 🌐 ## 🎯 Key Features http://localhost:3000
- 🔌## 📖 Documentation

### Development
- [Development Setup](docs/development/SETUP.md)
- [Contributing Guidelines](docs/development/CONTRIBUTING.md)
- [Testing Guide](docs/development/TESTING.md)

### Architecture
- [System Architecture](docs/architecture/SYSTEM_DESIGN.md)
- [API Reference](docs/api/REFERENCE.md)
- [Database Schema](docs/architecture/DATABASE.md)

### Deployment
- [Docker Deployment](docs/deployment/DOCKER.md)
- [Kubernetes Guide](docs/deployment/KUBERNETES.md)
- [Production Checklist](docs/deployment/PRODUCTION.md) | **Quick reference:** [QUICK_START.md](./QUICK_START.md)

---

## Prerequisites

**Required:**
- Docker Desktop (20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- 4GB+ RAM (8GB recommended)
- 10GB+ disk space

**Optional:**
- Visual Studio Code with Dev Containers extension
- Python 3.11+ (for local development without Docker)
- Git

## Architecture

### 💻 Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 14+ with pgvector
- **Cache**: Redis 6+ with Sentinel
- **Queue**: Celery + RabbitMQ
- **Auth**: OAuth2 + JWT + MFA

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI**: React 18 + TypeScript
- **Styling**: TailwindCSS + shadcn/ui
- **State**: Zustand + React Query
- **Charts**: Recharts + D3.js

### Infrastructure
- **Containers**: Docker + Docker Compose
- **Orchestration**: Kubernetes (EKS/GKE/AKS)
- **Monitoring**: Prometheus + Grafana + Loki
- **CI/CD**: GitHub Actions
- **Cloud**: AWS/GCP/Azure readybeddings

### Project Structure

```
/
├── .github/              # GitHub Actions workflows
├── docs/                 # Project documentation and guides
│   └── reports/          # Status reports and summaries
├── src/                  # All source code
│   ├── backend/          # FastAPI backend application
│   └── scripts/          # Agent scripts and other utilities
├── frontend/             # Next.js frontend application
├── tests/                # Test suites
├── .gitignore
├── docker-compose.yml
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Development

### Dependencies

- **Python services:** `pip install -r requirements.txt` installs pinned versions consumed by scripts and microservices. Service-specific extras live alongside each microservice (e.g., `services/value-architect/requirements.txt`).
- **Node frontend:** `npm install` respects the committed `package-lock.json` to guarantee reproducible builds.

### Running the Application

For targeted service development you can run components individually:

**Microservices (FastAPI):**

```bash
# Example: Value Architect service
cd services/value-architect
uvicorn main:app --reload --host 0.0.0.0 --port 8001
# Docs: http://localhost:8001/docs
```

The billing engine lives in `billing-system/backend/billing_service.py` and exposes documentation at `/api/docs` when run via `uvicorn` or Docker.

**Frontend (Next.js):**

```bash
cd frontend
npm install
npm run dev
# App: http://localhost:3000
```

### Code Quality

This project uses `ruff` for Python linting and formatting.

```bash
# Run from the root directory
ruff check --fix src/
ruff format src/
```

## AI-Powered Development

ValueVerse features an automated development system that uses AI to generate code from GitHub issues.

### How it Works

1.  Create an issue and label it with `generate-ui`.
2.  The "AI UI Generator" workflow is triggered.
3.  A multi-agent system analyzes the request, plans the architecture, generates the code, and creates a pull request.

The agent scripts that power this workflow are located in `src/scripts/agents/`.

---

**Built for the value economy**
