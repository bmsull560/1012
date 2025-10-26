import os
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

# Initialize FastAPI app
app = FastAPI(
    title="Value Executor Service",
    description="Executes value realization strategies and tracks implementation progress",
    version="1.0.0"
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Redis client for caching and task queue
redis_client = None

# ==================== Models ====================

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class ExecutionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ValueStrategy(BaseModel):
    """Value realization strategy definition"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    target_value: float
    timeline_days: int
    milestones: List[Dict[str, Any]]
    dependencies: List[UUID] = []
    priority: ExecutionPriority = ExecutionPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionTask(BaseModel):
    """Individual execution task"""
    id: UUID = Field(default_factory=uuid4)
    strategy_id: UUID
    name: str
    description: str
    assigned_to: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    progress: int = Field(ge=0, le=100, default=0)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str = ""
    blockers: List[str] = []

class ExecutionRequest(BaseModel):
    """Request to execute a value strategy"""
    strategy_id: UUID
    executor_id: str
    priority: ExecutionPriority = ExecutionPriority.MEDIUM
    target_completion: Optional[datetime] = None
    auto_assign_tasks: bool = True
    notify_stakeholders: bool = True

class ExecutionProgress(BaseModel):
    """Progress update for an execution"""
    task_id: UUID
    progress: int = Field(ge=0, le=100)
    status: ExecutionStatus
    notes: Optional[str] = None
    blockers: Optional[List[str]] = []

# ==================== Service Logic ====================

class ExecutorService:
    """Core execution service logic"""
    
    def __init__(self):
        self.strategies: Dict[UUID, ValueStrategy] = {}
        self.tasks: Dict[UUID, ExecutionTask] = {}
        self.executions: Dict[UUID, Dict] = {}
    
    async def create_strategy(self, strategy: ValueStrategy) -> ValueStrategy:
        """Create a new value realization strategy"""
        self.strategies[strategy.id] = strategy
        
        # Cache in Redis if available
        if redis_client:
            await redis_client.setex(
                f"strategy:{strategy.id}",
                3600,  # 1 hour TTL
                strategy.json()
            )
        
        return strategy
    
    async def execute_strategy(self, request: ExecutionRequest) -> Dict[str, Any]:
        """Execute a value realization strategy"""
        strategy = self.strategies.get(request.strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        execution_id = uuid4()
        tasks = []
        
        # Create tasks from strategy milestones
        for idx, milestone in enumerate(strategy.milestones):
            task = ExecutionTask(
                strategy_id=strategy.id,
                name=milestone.get("name", f"Task {idx+1}"),
                description=milestone.get("description", ""),
                due_date=milestone.get("due_date"),
                status=ExecutionStatus.PENDING
            )
            
            if request.auto_assign_tasks:
                task.assigned_to = request.executor_id
            
            self.tasks[task.id] = task
            tasks.append(task)
        
        # Store execution record
        self.executions[execution_id] = {
            "id": execution_id,
            "strategy_id": strategy.id,
            "executor_id": request.executor_id,
            "tasks": [task.id for task in tasks],
            "status": ExecutionStatus.IN_PROGRESS,
            "started_at": datetime.utcnow(),
            "priority": request.priority
        }
        
        return {
            "execution_id": str(execution_id),
            "strategy": strategy.dict(),
            "tasks": [task.dict() for task in tasks],
            "status": ExecutionStatus.IN_PROGRESS
        }
    
    async def update_progress(self, progress: ExecutionProgress) -> ExecutionTask:
        """Update execution progress"""
        task = self.tasks.get(progress.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.progress = progress.progress
        task.status = progress.status
        
        if progress.notes:
            task.notes = progress.notes
        
        if progress.blockers:
            task.blockers = progress.blockers
        
        if progress.status == ExecutionStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        
        # Update in cache
        if redis_client:
            await redis_client.setex(
                f"task:{task.id}",
                3600,
                task.json()
            )
        
        return task
    
    async def get_execution_status(self, execution_id: UUID) -> Dict[str, Any]:
        """Get current execution status"""
        execution = self.executions.get(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        tasks = [self.tasks[task_id] for task_id in execution["tasks"]]
        
        # Calculate overall progress
        total_progress = sum(task.progress for task in tasks)
        overall_progress = total_progress / len(tasks) if tasks else 0
        
        # Determine overall status
        if all(task.status == ExecutionStatus.COMPLETED for task in tasks):
            execution["status"] = ExecutionStatus.COMPLETED
        elif any(task.status == ExecutionStatus.FAILED for task in tasks):
            execution["status"] = ExecutionStatus.FAILED
        
        return {
            **execution,
            "overall_progress": overall_progress,
            "tasks": [task.dict() for task in tasks]
        }

# Initialize service
executor_service = ExecutorService()

# ==================== API Endpoints ====================

@app.get("/")
def read_root():
    return {
        "service": "Value Executor",
        "version": "1.0.0",
        "status": "operational",
        "description": "Executes value realization strategies"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "api": "operational",
            "redis": "unknown"
        }
    }
    
    # Check Redis connection
    if redis_client:
        try:
            await redis_client.ping()
            health_status["checks"]["redis"] = "connected"
        except:
            health_status["checks"]["redis"] = "disconnected"
    
    return health_status

@app.post("/strategies", response_model=ValueStrategy)
async def create_strategy(strategy: ValueStrategy):
    """Create a new value realization strategy"""
    return await executor_service.create_strategy(strategy)

@app.post("/execute")
async def execute_strategy(request: ExecutionRequest):
    """Execute a value realization strategy"""
    return await executor_service.execute_strategy(request)

@app.put("/progress")
async def update_progress(progress: ExecutionProgress):
    """Update task execution progress"""
    task = await executor_service.update_progress(progress)
    return {"message": "Progress updated", "task": task.dict()}

@app.get("/executions/{execution_id}")
async def get_execution_status(execution_id: UUID):
    """Get execution status and details"""
    return await executor_service.get_execution_status(execution_id)

@app.get("/tasks")
async def list_tasks(
    status: Optional[ExecutionStatus] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """List execution tasks with optional filters"""
    tasks = list(executor_service.tasks.values())
    
    if status:
        tasks = [t for t in tasks if t.status == status]
    
    if assigned_to:
        tasks = [t for t in tasks if t.assigned_to == assigned_to]
    
    return {
        "tasks": [task.dict() for task in tasks[:limit]],
        "total": len(tasks)
    }

@app.get("/strategies")
async def list_strategies():
    """List all value realization strategies"""
    return {
        "strategies": [s.dict() for s in executor_service.strategies.values()],
        "total": len(executor_service.strategies)
    }

# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global redis_client
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        redis_client = None

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if redis_client:
        await redis_client.close()

@app.get("/api/v1/metrics")
async def metrics():
    return {"service": "Value Executor", "uptime": "99.9%"}

if __name__ == "__main__":
    import uvicorn
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
