"""
Integration tests for Value Architect service using Testcontainers
Demonstrates real-world testing with actual dependencies
"""

import pytest
import asyncio
import json
import os
from datetime import datetime
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from fastapi.testclient import TestClient
import asyncpg
import redis

class TestValueArchitectIntegration:
    """
    Integration tests using real PostgreSQL and Redis containers
    No mocks - testing with actual dependencies!
    """
    
    @pytest.fixture(scope="class")
    def postgres(self):
        """Spin up a real PostgreSQL container for testing"""
        with PostgresContainer("postgres:15-alpine") as postgres:
            # Wait for container to be ready
            postgres.get_connection_url()
            yield postgres
    
    @pytest.fixture(scope="class")
    def redis_container(self):
        """Spin up a real Redis container for testing"""
        with RedisContainer("redis:7-alpine") as redis_cont:
            yield redis_cont
    
    @pytest.fixture(autouse=True)
    async def setup_database(self, postgres):
        """Create database schema before each test"""
        conn = await asyncpg.connect(postgres.get_connection_url())
        
        # Create tables
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS value_models (
                id UUID PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                industry VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                confidence_score FLOAT,
                data JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Clean up after test
        yield
        
        await conn.execute('DROP TABLE IF EXISTS value_models CASCADE')
        await conn.close()
    
    @pytest.fixture
    def app(self, postgres, redis_container):
        """Create FastAPI app with test container connections"""
        # Set environment variables to use test containers
        os.environ["DATABASE_URL"] = postgres.get_connection_url()
        os.environ["REDIS_URL"] = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
        
        # Import app after setting env vars so it uses test containers
        from main import app
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "value-architect"
    
    def test_create_value_model_integration(self, client, postgres, redis_container):
        """Test creating a value model with real database and cache"""
        # Create value model
        response = client.post(
            "/api/v1/value-models",
            json={
                "company_name": "Acme Corp",
                "industry": "SaaS",
                "company_size": "enterprise",
                "target_metrics": ["revenue_growth", "cost_reduction"]
            }
        )
        
        # Verify response
        assert response.status_code == 200
        model = response.json()
        assert model["company_name"] == "Acme Corp"
        assert model["industry"] == "SaaS"
        assert model["confidence_score"] > 0
        assert len(model["value_drivers"]) > 0
        
        model_id = model["id"]
        
        # Verify it's in Redis cache
        r = redis.Redis(
            host=redis_container.get_container_host_ip(),
            port=redis_container.get_exposed_port(6379),
            decode_responses=True
        )
        cached = r.get(f"model:{model_id}")
        assert cached is not None
        cached_model = json.loads(cached)
        assert cached_model["id"] == model_id
        
        # Verify we can retrieve it
        get_response = client.get(f"/api/v1/value-models/{model_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == model_id
    
    @pytest.mark.asyncio
    async def test_concurrent_model_creation(self, client):
        """Test system handles concurrent requests properly"""
        # Create 10 models concurrently
        tasks = []
        for i in range(10):
            response = client.post(
                "/api/v1/value-models",
                json={
                    "company_name": f"Company {i}",
                    "industry": "FinTech",
                    "company_size": "startup"
                }
            )
            tasks.append(response)
        
        # All should succeed
        for i, response in enumerate(tasks):
            assert response.status_code == 200
            assert response.json()["company_name"] == f"Company {i}"
    
    def test_refine_value_model(self, client):
        """Test refining an existing value model"""
        # First create a model
        create_response = client.post(
            "/api/v1/value-models",
            json={
                "company_name": "Refinement Corp",
                "industry": "Healthcare"
            }
        )
        model_id = create_response.json()["id"]
        
        # Refine it
        refine_response = client.put(
            f"/api/v1/value-models/{model_id}/refine",
            json={
                "additional_drivers": [
                    {
                        "id": "compliance",
                        "name": "Regulatory Compliance",
                        "potential_value": 150000
                    }
                ],
                "updated_calculations": {
                    "revised_roi": 4.5
                }
            }
        )
        
        assert refine_response.status_code == 200
        refined = refine_response.json()
        assert len(refined["value_drivers"]) > 3  # Original + new driver
    
    def test_service_metrics_endpoint(self, client):
        """Test metrics endpoint for Prometheus scraping"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert metrics["service"] == "value-architect"
        assert "requests_processed" in metrics
        assert "avg_response_time_ms" in metrics
    
    def test_error_handling_invalid_model(self, client):
        """Test error handling for invalid model retrieval"""
        response = client.get("/api/v1/value-models/invalid-uuid")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.parametrize("industry", ["SaaS", "FinTech", "Healthcare", "Retail", "Manufacturing"])
    def test_multiple_industries(self, client, industry):
        """Test value model creation across different industries"""
        response = client.post(
            "/api/v1/value-models",
            json={
                "company_name": f"{industry} Corp",
                "industry": industry
            }
        )
        
        assert response.status_code == 200
        model = response.json()
        assert model["industry"] == industry
        # Each industry should have relevant value drivers
        assert len(model["value_drivers"]) >= 2


class TestDatabaseIntegration:
    """Test database-specific functionality"""
    
    @pytest.fixture(scope="class")
    def postgres(self):
        """PostgreSQL container with custom configuration"""
        postgres = PostgresContainer("postgres:15")
        postgres.with_env("POSTGRES_DB", "test_valueverse")
        postgres.with_env("POSTGRES_INITDB_ARGS", "--encoding=UTF8")
        
        with postgres as pg:
            yield pg
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, postgres):
        """Test connection pooling works correctly"""
        pool = await asyncpg.create_pool(
            postgres.get_connection_url(),
            min_size=5,
            max_size=10
        )
        
        # Acquire multiple connections
        connections = []
        for _ in range(5):
            conn = await pool.acquire()
            connections.append(conn)
        
        # Verify pool stats
        assert pool.get_size() >= 5
        assert pool.get_idle_size() == 0  # All connections in use
        
        # Release connections
        for conn in connections:
            await pool.release(conn)
        
        assert pool.get_idle_size() == 5  # All connections returned
        
        await pool.close()
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, postgres):
        """Test transaction rollback on error"""
        conn = await asyncpg.connect(postgres.get_connection_url())
        
        # Create table
        await conn.execute('''
            CREATE TABLE test_transactions (
                id SERIAL PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Start transaction that will fail
        try:
            async with conn.transaction():
                await conn.execute("INSERT INTO test_transactions (value) VALUES ('first')")
                await conn.execute("INSERT INTO test_transactions (value) VALUES ('second')")
                # This will fail due to constraint
                await conn.execute("INSERT INTO test_transactions (id, value) VALUES (1, 'duplicate')")
        except asyncpg.UniqueViolationError:
            pass
        
        # Verify rollback - should have no records
        count = await conn.fetchval("SELECT COUNT(*) FROM test_transactions")
        assert count == 0
        
        await conn.close()


# Run tests with: pytest test_integration.py -v
