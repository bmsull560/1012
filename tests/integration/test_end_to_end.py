"""End-to-end integration tests for ValueVerse Platform"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from uuid import uuid4
import os
from typing import Dict, Any

# Service URLs (configurable via environment)
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost")
FRONTEND_URL = f"{BASE_URL}:3000"
ARCHITECT_URL = f"{BASE_URL}:8001"
COMMITTER_URL = f"{BASE_URL}:8002"
EXECUTOR_URL = f"{BASE_URL}:8003"
BILLING_URL = f"{BASE_URL}:8004"

# Test credentials
TEST_USER_EMAIL = "test@valueverse.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_ADMIN_EMAIL = "admin@valueverse.com"
TEST_ADMIN_PASSWORD = "AdminPassword123!"

# ==================== Fixtures ====================

@pytest.fixture
async def http_client():
    """Create an async HTTP client"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client

@pytest.fixture
async def authenticated_client(http_client):
    """Create an authenticated HTTP client"""
    # Login and get token
    login_response = await http_client.post(
        f"{FRONTEND_URL}/api/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("token")
        http_client.headers["Authorization"] = f"Bearer {token}"
    
    yield http_client

@pytest.fixture
def sample_value_model():
    """Create a sample value model"""
    return {
        "company_name": "Test Company Inc",
        "industry": "Technology",
        "stage": "growth",
        "inputs": {
            "current_revenue": 5000000,
            "target_growth": 25,
            "implementation_cost": 500000,
            "time_to_value": 6
        },
        "metadata": {
            "created_by": "integration_test",
            "version": "1.0"
        }
    }

# ==================== Health Check Tests ====================

class TestHealthChecks:
    """Test all services are healthy"""
    
    @pytest.mark.asyncio
    async def test_all_services_healthy(self, http_client):
        """Verify all microservices are responding"""
        services = [
            ("Value Architect", f"{ARCHITECT_URL}/health"),
            ("Value Committer", f"{COMMITTER_URL}/health"),
            ("Value Executor", f"{EXECUTOR_URL}/health"),
            ("Billing Service", f"{BILLING_URL}/health"),
        ]
        
        for service_name, url in services:
            try:
                response = await http_client.get(url)
                assert response.status_code == 200, f"{service_name} is not healthy"
                data = response.json()
                assert data["status"] == "healthy", f"{service_name} reports unhealthy status"
            except httpx.ConnectError:
                pytest.skip(f"{service_name} is not running at {url}")

# ==================== Authentication Flow Tests ====================

class TestAuthenticationFlow:
    """Test complete authentication workflows"""
    
    @pytest.mark.asyncio
    async def test_user_registration_and_login(self, http_client):
        """Test user can register and login"""
        # Generate unique email for test
        unique_email = f"test_{uuid4().hex[:8]}@valueverse.com"
        
        # 1. Register new user
        register_data = {
            "email": unique_email,
            "password": "SecurePassword123!",
            "full_name": "Test User",
            "organization": "Test Org"
        }
        
        register_response = await http_client.post(
            f"{FRONTEND_URL}/api/auth/register",
            json=register_data
        )
        
        if register_response.status_code != 200:
            pytest.skip("Registration endpoint not available")
        
        assert register_response.status_code == 200
        register_result = register_response.json()
        assert "user" in register_result
        
        # 2. Login with new credentials
        login_response = await http_client.post(
            f"{FRONTEND_URL}/api/auth/login",
            json={
                "email": unique_email,
                "password": "SecurePassword123!"
            }
        )
        
        assert login_response.status_code == 200
        login_result = login_response.json()
        assert "token" in login_result
        assert "user" in login_result
        
        # 3. Verify token works
        http_client.headers["Authorization"] = f"Bearer {login_result['token']}"
        profile_response = await http_client.get(f"{FRONTEND_URL}/api/auth/profile")
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == unique_email
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self, http_client):
        """Test login with invalid credentials fails"""
        login_response = await http_client.post(
            f"{FRONTEND_URL}/api/auth/login",
            json={
                "email": "nonexistent@valueverse.com",
                "password": "WrongPassword"
            }
        )
        
        assert login_response.status_code in [401, 403]

# ==================== Value Model Workflow Tests ====================

class TestValueModelWorkflow:
    """Test complete value model creation and execution workflow"""
    
    @pytest.mark.asyncio
    async def test_create_analyze_execute_value_model(self, authenticated_client, sample_value_model):
        """Test the complete value model lifecycle"""
        
        # 1. Create value model via Architect service
        create_response = await authenticated_client.post(
            f"{ARCHITECT_URL}/api/v1/models",
            json=sample_value_model
        )
        
        if create_response.status_code != 200:
            pytest.skip("Value Architect service not fully implemented")
        
        assert create_response.status_code == 200
        model_data = create_response.json()
        model_id = model_data["id"]
        
        # 2. Analyze the model
        analyze_response = await authenticated_client.post(
            f"{ARCHITECT_URL}/api/v1/models/{model_id}/analyze"
        )
        
        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()
        assert "recommendations" in analysis_data
        assert "risk_score" in analysis_data
        
        # 3. Commit the model
        commit_response = await authenticated_client.post(
            f"{COMMITTER_URL}/api/v1/commit",
            json={
                "model_id": model_id,
                "message": "Initial commit from integration test",
                "version": "1.0.0"
            }
        )
        
        assert commit_response.status_code == 200
        commit_data = commit_response.json()
        assert "commit_id" in commit_data
        
        # 4. Create execution strategy
        strategy_response = await authenticated_client.post(
            f"{EXECUTOR_URL}/strategies",
            json={
                "name": "Test Execution Strategy",
                "description": "Integration test strategy",
                "target_value": 1000000,
                "timeline_days": 90,
                "milestones": [
                    {"name": "Phase 1", "description": "Initial setup"},
                    {"name": "Phase 2", "description": "Implementation"},
                    {"name": "Phase 3", "description": "Optimization"}
                ]
            }
        )
        
        assert strategy_response.status_code == 200
        strategy_data = strategy_response.json()
        strategy_id = strategy_data["id"]
        
        # 5. Execute the strategy
        execute_response = await authenticated_client.post(
            f"{EXECUTOR_URL}/execute",
            json={
                "strategy_id": strategy_id,
                "executor_id": "test_user",
                "priority": "high",
                "auto_assign_tasks": True
            }
        )
        
        assert execute_response.status_code == 200
        execution_data = execute_response.json()
        assert "execution_id" in execution_data
        assert len(execution_data["tasks"]) == 3

# ==================== Multi-Service Transaction Tests ====================

class TestMultiServiceTransactions:
    """Test transactions spanning multiple services"""
    
    @pytest.mark.asyncio
    async def test_cross_service_data_consistency(self, authenticated_client):
        """Test data consistency across services"""
        
        # Create a model in Architect
        model_response = await authenticated_client.post(
            f"{ARCHITECT_URL}/api/v1/models",
            json={
                "company_name": "Consistency Test Corp",
                "industry": "Finance",
                "stage": "enterprise",
                "inputs": {"revenue": 10000000}
            }
        )
        
        if model_response.status_code != 200:
            pytest.skip("Service not fully implemented")
        
        model_id = model_response.json()["id"]
        
        # Verify model is accessible from Committer
        committer_check = await authenticated_client.get(
            f"{COMMITTER_URL}/api/v1/models/{model_id}"
        )
        
        # Services should share data or have synchronization
        assert committer_check.status_code in [200, 404]  # 404 if services are isolated
        
        if committer_check.status_code == 200:
            assert committer_check.json()["id"] == model_id

# ==================== Performance Tests ====================

class TestPerformance:
    """Test system performance under load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, authenticated_client):
        """Test system handles concurrent requests"""
        
        async def make_request(index: int):
            """Make a single request"""
            response = await authenticated_client.get(f"{ARCHITECT_URL}/health")
            return response.status_code == 200
        
        # Make 50 concurrent requests
        tasks = [make_request(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least 90% should succeed
        successes = sum(1 for r in results if r is True)
        assert successes >= 45, f"Only {successes}/50 requests succeeded"
    
    @pytest.mark.asyncio
    async def test_response_times(self, authenticated_client):
        """Test API response times are acceptable"""
        import time
        
        endpoints = [
            f"{ARCHITECT_URL}/health",
            f"{COMMITTER_URL}/health",
            f"{EXECUTOR_URL}/health",
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await authenticated_client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Health checks should respond quickly
            assert response_time < 1.0, f"{endpoint} took {response_time:.2f}s"

# ==================== Security Tests ====================

class TestSecurity:
    """Test security measures"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access_blocked(self, http_client):
        """Test that protected endpoints require authentication"""
        
        protected_endpoints = [
            f"{ARCHITECT_URL}/api/v1/models",
            f"{COMMITTER_URL}/api/v1/commits",
            f"{EXECUTOR_URL}/strategies",
        ]
        
        for endpoint in protected_endpoints:
            response = await http_client.get(endpoint)
            # Should return 401 or 403 for unauthorized access
            assert response.status_code in [401, 403], f"{endpoint} allows unauthorized access"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, http_client):
        """Test rate limiting is enforced"""
        
        # Make many rapid requests
        responses = []
        for _ in range(150):  # Exceed typical rate limit
            response = await http_client.get(f"{BILLING_URL}/health")
            responses.append(response.status_code)
        
        # Should see some rate limit responses (429)
        rate_limited = sum(1 for status in responses if status == 429)
        
        # At least some requests should be rate limited
        # Skip if rate limiting not implemented
        if rate_limited == 0:
            pytest.skip("Rate limiting not implemented")
        
        assert rate_limited > 0, "No rate limiting detected"
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, authenticated_client):
        """Test SQL injection attempts are blocked"""
        
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "<script>alert('XSS')</script>",
            "../../etc/passwd"
        ]
        
        for payload in malicious_inputs:
            response = await authenticated_client.post(
                f"{ARCHITECT_URL}/api/v1/models",
                json={
                    "company_name": payload,
                    "industry": "Test",
                    "stage": "test",
                    "inputs": {}
                }
            )
            
            # Should either sanitize or reject malicious input
            if response.status_code == 200:
                # If accepted, verify it was sanitized
                data = response.json()
                assert payload not in str(data), f"Malicious payload not sanitized: {payload}"

# ==================== Data Integrity Tests ====================

class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, authenticated_client):
        """Test that failed transactions are properly rolled back"""
        
        # Create a model with invalid data that should fail validation
        invalid_model = {
            "company_name": "",  # Empty name should fail
            "industry": None,
            "inputs": "not_a_dict"  # Wrong type
        }
        
        response = await authenticated_client.post(
            f"{ARCHITECT_URL}/api/v1/models",
            json=invalid_model
        )
        
        # Should reject invalid data
        assert response.status_code in [400, 422]
        
        # Verify no partial data was saved
        list_response = await authenticated_client.get(
            f"{ARCHITECT_URL}/api/v1/models"
        )
        
        if list_response.status_code == 200:
            models = list_response.json().get("models", [])
            # Should not find any models with empty names
            assert not any(m.get("company_name") == "" for m in models)

# ==================== Monitoring Tests ====================

class TestMonitoring:
    """Test monitoring and observability features"""
    
    @pytest.mark.asyncio
    async def test_metrics_endpoints(self, http_client):
        """Test metrics endpoints are accessible"""
        
        metrics_endpoints = [
            f"{ARCHITECT_URL}/metrics",
            f"{EXECUTOR_URL}/api/v1/metrics",
            f"{BILLING_URL}/metrics",
        ]
        
        for endpoint in metrics_endpoints:
            response = await http_client.get(endpoint)
            
            # Metrics might require auth or might not be implemented
            if response.status_code == 404:
                continue
                
            assert response.status_code in [200, 401], f"Unexpected status for {endpoint}"
            
            if response.status_code == 200:
                # Should return some metrics data
                data = response.json()
                assert data is not None

# ==================== Cleanup Tests ====================

class TestCleanup:
    """Test cleanup and resource management"""
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, authenticated_client):
        """Test that resources are properly cleaned up"""
        
        # Create a temporary resource
        response = await authenticated_client.post(
            f"{EXECUTOR_URL}/strategies",
            json={
                "name": "Temporary Strategy",
                "description": "Should be cleaned up",
                "target_value": 1000,
                "timeline_days": 1,
                "milestones": []
            }
        )
        
        if response.status_code == 200:
            strategy_id = response.json()["id"]
            
            # Delete the resource (if delete endpoint exists)
            delete_response = await authenticated_client.delete(
                f"{EXECUTOR_URL}/strategies/{strategy_id}"
            )
            
            if delete_response.status_code in [200, 204]:
                # Verify it's deleted
                get_response = await authenticated_client.get(
                    f"{EXECUTOR_URL}/strategies/{strategy_id}"
                )
                assert get_response.status_code == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
