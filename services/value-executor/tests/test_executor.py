"""Unit tests for Value Executor Service"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, ExecutorService, ValueStrategy, ExecutionRequest, ExecutionProgress, ExecutionStatus, ExecutionPriority

client = TestClient(app)

# ==================== Fixtures ====================

@pytest.fixture
def executor_service():
    """Create a fresh executor service instance for each test"""
    return ExecutorService()

@pytest.fixture
def sample_strategy():
    """Create a sample value strategy"""
    return ValueStrategy(
        name="Q4 Revenue Growth Strategy",
        description="Increase revenue by 25% through new product launches",
        target_value=1000000.0,
        timeline_days=90,
        milestones=[
            {
                "name": "Market Research",
                "description": "Complete market analysis",
                "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat()
            },
            {
                "name": "Product Development",
                "description": "Develop MVP",
                "due_date": (datetime.utcnow() + timedelta(days=45)).isoformat()
            },
            {
                "name": "Launch Campaign",
                "description": "Execute go-to-market strategy",
                "due_date": (datetime.utcnow() + timedelta(days=75)).isoformat()
            }
        ],
        priority=ExecutionPriority.HIGH
    )

@pytest.fixture
def sample_execution_request():
    """Create a sample execution request"""
    return ExecutionRequest(
        strategy_id=uuid4(),
        executor_id="user-123",
        priority=ExecutionPriority.HIGH,
        auto_assign_tasks=True,
        notify_stakeholders=True
    )

# ==================== Unit Tests ====================

class TestExecutorService:
    """Test the ExecutorService class"""
    
    @pytest.mark.asyncio
    async def test_create_strategy(self, executor_service, sample_strategy):
        """Test creating a new strategy"""
        result = await executor_service.create_strategy(sample_strategy)
        
        assert result.id == sample_strategy.id
        assert result.name == sample_strategy.name
        assert result.target_value == sample_strategy.target_value
        assert sample_strategy.id in executor_service.strategies
    
    @pytest.mark.asyncio
    async def test_execute_strategy(self, executor_service, sample_strategy, sample_execution_request):
        """Test executing a strategy"""
        # First create the strategy
        await executor_service.create_strategy(sample_strategy)
        sample_execution_request.strategy_id = sample_strategy.id
        
        # Execute the strategy
        result = await executor_service.execute_strategy(sample_execution_request)
        
        assert "execution_id" in result
        assert result["status"] == ExecutionStatus.IN_PROGRESS
        assert len(result["tasks"]) == len(sample_strategy.milestones)
        
        # Verify tasks were created
        for task in result["tasks"]:
            assert task["strategy_id"] == sample_strategy.id
            assert task["assigned_to"] == sample_execution_request.executor_id
            assert task["status"] == ExecutionStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_strategy(self, executor_service, sample_execution_request):
        """Test executing a strategy that doesn't exist"""
        with pytest.raises(Exception) as exc_info:
            await executor_service.execute_strategy(sample_execution_request)
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_update_progress(self, executor_service, sample_strategy, sample_execution_request):
        """Test updating task progress"""
        # Setup: create and execute strategy
        await executor_service.create_strategy(sample_strategy)
        sample_execution_request.strategy_id = sample_strategy.id
        execution_result = await executor_service.execute_strategy(sample_execution_request)
        
        task_id = execution_result["tasks"][0]["id"]
        
        # Update progress
        progress = ExecutionProgress(
            task_id=task_id,
            progress=50,
            status=ExecutionStatus.IN_PROGRESS,
            notes="Halfway complete"
        )
        
        updated_task = await executor_service.update_progress(progress)
        
        assert updated_task.progress == 50
        assert updated_task.status == ExecutionStatus.IN_PROGRESS
        assert updated_task.notes == "Halfway complete"
    
    @pytest.mark.asyncio
    async def test_get_execution_status(self, executor_service, sample_strategy, sample_execution_request):
        """Test getting execution status"""
        # Setup: create and execute strategy
        await executor_service.create_strategy(sample_strategy)
        sample_execution_request.strategy_id = sample_strategy.id
        execution_result = await executor_service.execute_strategy(sample_execution_request)
        
        execution_id = uuid4()
        # Manually set the execution ID for testing
        for key in list(executor_service.executions.keys()):
            executor_service.executions[execution_id] = executor_service.executions.pop(key)
            break
        
        # Get status
        status = await executor_service.get_execution_status(execution_id)
        
        assert status["strategy_id"] == sample_strategy.id
        assert status["executor_id"] == sample_execution_request.executor_id
        assert "overall_progress" in status
        assert status["overall_progress"] == 0  # All tasks start at 0 progress

# ==================== API Endpoint Tests ====================

class TestAPIEndpoints:
    """Test the FastAPI endpoints"""
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Value Executor"
        assert data["status"] == "operational"
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "checks" in data
    
    def test_create_strategy_endpoint(self, sample_strategy):
        """Test creating a strategy via API"""
        response = client.post(
            "/strategies",
            json=sample_strategy.dict()
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_strategy.name
        assert data["target_value"] == sample_strategy.target_value
    
    def test_execute_strategy_endpoint(self, sample_strategy):
        """Test executing a strategy via API"""
        # First create the strategy
        create_response = client.post(
            "/strategies",
            json=sample_strategy.dict()
        )
        strategy_id = create_response.json()["id"]
        
        # Execute the strategy
        execution_request = {
            "strategy_id": strategy_id,
            "executor_id": "test-user",
            "priority": "high",
            "auto_assign_tasks": True,
            "notify_stakeholders": False
        }
        
        response = client.post("/execute", json=execution_request)
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert data["status"] == "in_progress"
        assert len(data["tasks"]) > 0
    
    def test_list_strategies_endpoint(self, sample_strategy):
        """Test listing strategies"""
        # Create a strategy first
        client.post("/strategies", json=sample_strategy.dict())
        
        response = client.get("/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_list_tasks_endpoint(self):
        """Test listing tasks with filters"""
        response = client.get("/tasks?status=pending&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data

# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_execution_workflow(self, sample_strategy):
        """Test the complete workflow from strategy creation to task completion"""
        # 1. Create strategy
        strategy_response = client.post("/strategies", json=sample_strategy.dict())
        assert strategy_response.status_code == 200
        strategy_id = strategy_response.json()["id"]
        
        # 2. Execute strategy
        execution_request = {
            "strategy_id": strategy_id,
            "executor_id": "test-user",
            "priority": "high",
            "auto_assign_tasks": True,
            "notify_stakeholders": False
        }
        execute_response = client.post("/execute", json=execution_request)
        assert execute_response.status_code == 200
        execution_data = execute_response.json()
        
        # 3. Update task progress
        task_id = execution_data["tasks"][0]["id"]
        progress_update = {
            "task_id": task_id,
            "progress": 100,
            "status": "completed",
            "notes": "Task completed successfully"
        }
        progress_response = client.put("/progress", json=progress_update)
        assert progress_response.status_code == 200
        
        # 4. Verify task completion
        updated_task = progress_response.json()["task"]
        assert updated_task["progress"] == 100
        assert updated_task["status"] == "completed"

# ==================== Performance Tests ====================

class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_strategy_creation(self, executor_service):
        """Test creating multiple strategies concurrently"""
        strategies = [
            ValueStrategy(
                name=f"Strategy {i}",
                description=f"Description {i}",
                target_value=float(i * 10000),
                timeline_days=30,
                milestones=[],
                priority=ExecutionPriority.MEDIUM
            )
            for i in range(10)
        ]
        
        # Create strategies concurrently
        tasks = [executor_service.create_strategy(s) for s in strategies]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert len(executor_service.strategies) == 10
    
    def test_api_response_time(self):
        """Test API response times are acceptable"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 0.1  # Should respond in less than 100ms

# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_strategy_data(self):
        """Test creating strategy with invalid data"""
        invalid_strategy = {
            "name": "",  # Empty name
            "target_value": -1000,  # Negative value
            "timeline_days": "not_a_number"  # Invalid type
        }
        
        response = client.post("/strategies", json=invalid_strategy)
        assert response.status_code == 422  # Validation error
    
    def test_update_nonexistent_task(self):
        """Test updating a task that doesn't exist"""
        progress_update = {
            "task_id": str(uuid4()),
            "progress": 50,
            "status": "in_progress"
        }
        
        response = client.put("/progress", json=progress_update)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, executor_service):
        """Test service behavior when Redis is unavailable"""
        with patch('main.redis_client', None):
            # Service should still work without Redis
            strategy = ValueStrategy(
                name="Test Strategy",
                description="Test",
                target_value=1000.0,
                timeline_days=30,
                milestones=[]
            )
            
            result = await executor_service.create_strategy(strategy)
            assert result is not None
            assert result.id == strategy.id

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
