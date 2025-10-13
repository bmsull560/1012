"""API v1 router aggregation"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, value_models, workspace, agents

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(value_models.router, prefix="/value-models", tags=["value-models"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
