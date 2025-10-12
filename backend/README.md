# ValueVerse Backend

FastAPI-based backend service for the ValueVerse Platform.

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Agent Orchestration**: LangGraph + LangChain + CrewAI
- **Database**: PostgreSQL 15 + TimescaleDB (for time-series metrics)
- **Cache**: Redis 7
- **Task Queue**: Celery + RabbitMQ
- **AI Models**: GPT-4, Claude-3, Gemini-Pro
- **Vector Store**: Pinecone (for embeddings)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration management
│   │
│   ├── api/                       # API endpoints
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── workspace.py       # Unified workspace endpoints
│   │   │   ├── value_graph.py     # Value graph operations
│   │   │   ├── agents.py          # Agent interaction endpoints
│   │   │   └── knowledge.py       # Knowledge base endpoints
│   │   └── dependencies.py        # Shared dependencies
│   │
│   ├── agents/                    # AI Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py                # Base agent class
│   │   ├── value_architect.py     # Pre-sales agent
│   │   ├── value_committer.py     # Sales agent
│   │   ├── value_executor.py      # Delivery agent
│   │   └── value_amplifier.py     # Customer success agent
│   │
│   ├── models/                    # Database models
│   │   ├── __init__.py
│   │   ├── value_graph.py         # Value graph schema
│   │   ├── user.py                # User models
│   │   └── knowledge_base.py      # Knowledge base models
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── value.py               # Value-related schemas
│   │   ├── agent.py               # Agent request/response schemas
│   │   └── workspace.py           # Workspace schemas
│   │
│   ├── services/                  # Business logic services
│   │   ├── __init__.py
│   │   ├── value_graph_service.py # Value graph operations
│   │   ├── agent_orchestrator.py  # Agent coordination
│   │   ├── knowledge_service.py   # Knowledge base automation
│   │   └── integration_service.py # External system integrations
│   │
│   ├── integrations/              # External system adapters
│   │   ├── __init__.py
│   │   ├── salesforce.py
│   │   ├── servicenow.py
│   │   ├── gainsight.py
│   │   └── netsuite.py
│   │
│   ├── core/                      # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py            # Auth & authorization
│   │   ├── database.py            # Database connection
│   │   ├── cache.py               # Redis operations
│   │   └── logging.py             # Logging configuration
│   │
│   └── tasks/                     # Celery tasks
│       ├── __init__.py
│       ├── knowledge_generation.py
│       └── value_tracking.py
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_agents/
│   ├── test_api/
│   └── test_services/
│
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
│
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Development dependencies
├── pyproject.toml                 # Project configuration
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with TimescaleDB extension
- Redis 7+
- (Optional) RabbitMQ for Celery tasks

### Installation

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run database migrations**:
```bash
alembic upgrade head
```

5. **Start the development server**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the API**:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Development

### Code Quality

```bash
# Format code
black .
isort .

# Lint
flake8 .

# Type checking
mypy .

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Running Celery Workers

```bash
# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info
```

## API Structure

### Core Endpoints

- **Workspace**: `/api/v1/workspace/*` - Unified workspace operations
- **Value Graph**: `/api/v1/value-graph/*` - Value graph CRUD and queries
- **Agents**: `/api/v1/agents/*` - Agent interactions and orchestration
- **Knowledge Base**: `/api/v1/knowledge/*` - Knowledge base management

### Authentication

All endpoints (except public ones) require OAuth2 authentication:

```python
Authorization: Bearer <access_token>
```

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `JWT_SECRET_KEY`: JWT secret for authentication

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents/test_value_architect.py

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Security

Following enterprise-grade security standards:

- ✅ Input validation with Pydantic
- ✅ OAuth2 + JWT authentication
- ✅ RBAC authorization
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Rate limiting on sensitive endpoints
- ✅ Secrets management via environment variables
- ✅ TLS/SSL in production

## Performance

Target performance metrics:

- Agent response time: < 500ms
- Value calculation time: < 2s
- Graph query performance: < 50ms
- API throughput: 1,000+ requests/second

## Documentation

- API documentation: http://localhost:8000/docs
- Technical architecture: `/docs/design_brief.md`
- Agent specifications: `/docs/operatingsystem.md`

## Contributing

See the main project README and coding guidelines in the IDE memory system.

---

**Status**: 🚧 Under Development
