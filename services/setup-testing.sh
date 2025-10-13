#!/bin/bash

# Setup Testcontainers testing environment for ValueVerse
set -e

echo "🧪 Setting up Testcontainers Testing Environment"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_success() {
    echo -e "${GREEN}✓${NC} $1"
}

echo_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Check prerequisites
echo_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python is required but not installed"
    exit 1
fi

echo_success "Prerequisites OK"

# Create virtual environment
echo_info "Creating Python virtual environment..."
python -m venv test-env
source test-env/bin/activate || . test-env/Scripts/activate

# Install testing dependencies
echo_info "Installing testing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements-test.txt

echo_success "Testing dependencies installed"

# Create test directories
echo_info "Creating test structure..."
for service in value-architect value-committer value-executor value-amplifier; do
    mkdir -p $service/tests/integration
    mkdir -p $service/tests/unit
    mkdir -p $service/tests/fixtures
    
    # Create __init__ files
    touch $service/tests/__init__.py
    touch $service/tests/integration/__init__.py
    touch $service/tests/unit/__init__.py
    touch $service/tests/fixtures/__init__.py
    
    echo_success "Created test directories for $service"
done

# Create shared fixtures
cat > value-architect/tests/fixtures/containers.py << 'EOF'
"""
Shared Testcontainers fixtures for all tests
"""
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def postgres():
    """Shared PostgreSQL container for entire test session"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def redis():
    """Shared Redis container for entire test session"""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis

@pytest.fixture
def test_db(postgres):
    """Get test database connection"""
    import asyncpg
    import asyncio
    
    async def get_conn():
        return await asyncpg.connect(postgres.get_connection_url())
    
    return asyncio.run(get_conn())

@pytest.fixture
def test_cache(redis):
    """Get test Redis client"""
    import redis as redis_client
    return redis_client.Redis(
        host=redis.get_container_host_ip(),
        port=redis.get_exposed_port(6379)
    )
EOF

# Create pytest configuration
cat > pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=term-missing
    --cov-report=html
    -n auto
markers =
    integration: Integration tests with real dependencies
    unit: Unit tests
    slow: Slow tests
    benchmark: Performance tests
EOF

# Create sample integration test
cat > value-architect/tests/integration/test_sample.py << 'EOF'
"""
Sample integration test using Testcontainers
"""
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.mark.integration
class TestSampleIntegration:
    
    def test_postgres_connection(self):
        """Test we can connect to PostgreSQL container"""
        with PostgresContainer("postgres:15") as postgres:
            conn_url = postgres.get_connection_url()
            assert "postgresql" in conn_url
            assert postgres.get_container_host_ip() is not None
    
    def test_redis_connection(self):
        """Test we can connect to Redis container"""
        with RedisContainer("redis:7") as redis:
            import redis as redis_client
            
            client = redis_client.Redis(
                host=redis.get_container_host_ip(),
                port=redis.get_exposed_port(6379)
            )
            
            # Test basic operations
            client.set("test_key", "test_value")
            assert client.get("test_key").decode() == "test_value"
    
    @pytest.mark.slow
    def test_multiple_containers(self):
        """Test running multiple containers together"""
        with PostgresContainer() as postgres, RedisContainer() as redis:
            # Both containers running
            assert postgres.get_connection_url() is not None
            assert redis.get_container_host_ip() is not None
            
            # Can interact with both
            import psycopg2
            import redis as redis_client
            
            # PostgreSQL
            pg_conn = psycopg2.connect(postgres.get_connection_url())
            cursor = pg_conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
            
            # Redis
            r_client = redis_client.Redis(
                host=redis.get_container_host_ip(),
                port=redis.get_exposed_port(6379)
            )
            r_client.ping()
EOF

echo_success "Created sample tests"

# Create test runner script
cat > run-tests.sh << 'EOF'
#!/bin/bash

# Test runner for ValueVerse microservices

SERVICE=${1:-all}
TYPE=${2:-all}

echo "🧪 Running tests..."

if [ "$SERVICE" == "all" ]; then
    SERVICES="value-architect value-committer value-executor value-amplifier"
else
    SERVICES=$SERVICE
fi

for svc in $SERVICES; do
    echo ""
    echo "Testing $svc..."
    echo "================================"
    
    cd $svc
    
    case $TYPE in
        unit)
            pytest tests/unit -v
            ;;
        integration)
            pytest tests/integration -v -m integration
            ;;
        all)
            pytest tests -v
            ;;
        *)
            echo "Usage: ./run-tests.sh [service|all] [unit|integration|all]"
            exit 1
            ;;
    esac
    
    cd ..
done

echo ""
echo "✅ Tests complete!"
echo ""
echo "📊 Coverage report: htmlcov/index.html"
EOF

chmod +x run-tests.sh

echo ""
echo "================================================"
echo_success "Testcontainers testing environment ready!"
echo ""
echo "📚 Quick Start:"
echo ""
echo "1. Activate virtual environment:"
echo "   source test-env/bin/activate"
echo ""
echo "2. Run sample test:"
echo "   cd value-architect"
echo "   pytest tests/integration/test_sample.py -v"
echo ""
echo "3. Run all tests:"
echo "   ./run-tests.sh"
echo ""
echo "4. Run specific service tests:"
echo "   ./run-tests.sh value-architect integration"
echo ""
echo "📊 Features configured:"
echo "  ✓ Parallel test execution"
echo "  ✓ Code coverage reporting"
echo "  ✓ Async test support"
echo "  ✓ Shared container fixtures"
echo "  ✓ Performance benchmarking"
echo ""
echo "🎯 Next steps:"
echo "  1. Copy test_integration.py to each service"
echo "  2. Run: pytest test_integration.py"
echo "  3. View coverage: open htmlcov/index.html"
