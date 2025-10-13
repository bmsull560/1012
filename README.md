# ValueVerse Platform

> The Value Realization Operating System - Transforming B2B relationships into perpetual value creation engines

## Overview

ValueVerse is an enterprise-grade platform that revolutionizes how businesses create, deliver, and prove customer value. By combining Living Value Graphs with Agentic Orchestration and an Adaptive Interface, ValueVerse transforms customer relationships from transactional to transformational.

## Quick Start

### Prerequisites

- **Docker Desktop** (4GB RAM minimum, 8GB recommended)
- **Visual Studio Code** with Dev Containers extension
- **Python 3.11+**
- **Git**

### Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd 1012
    ```

2.  **Open in VS Code and use the Dev Container:**

    - Open the project in VS Code (`code .`).
    - When prompted, click "Reopen in Container" or press F1 and select "Dev Containers: Reopen in Container".
    - The first build takes 3-5 minutes.

3.  **Set up the Python Environment:**
    The project now uses a virtual environment to manage dependencies.

    ```bash
    # Create the virtual environment
    python3 -m venv .venv

    # Activate the virtual environment
    source .venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
    ```

## Architecture

### Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI, LangGraph, PostgreSQL, Redis
- **AI Layer**: Together AI, LangChain, OpenAI Embeddings

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

### Running the Application

Ensure your virtual environment is activated (`source .venv/bin/activate`).

**Backend (FastAPI):**

```bash
cd src/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# API docs: http://localhost:8000/docs
```

**Frontend (Next.js):**

```bash
cd frontend
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
