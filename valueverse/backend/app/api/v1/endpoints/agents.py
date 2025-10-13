"""Agent endpoints"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_agents():
    """List available agents"""
    return [
        {"id": "architect", "name": "ValueArchitect", "status": "online"},
        {"id": "committer", "name": "ValueCommitter", "status": "online"},
        {"id": "executor", "name": "ValueExecutor", "status": "online"},
        {"id": "amplifier", "name": "ValueAmplifier", "status": "online"},
    ]
