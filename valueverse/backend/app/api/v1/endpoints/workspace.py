"""Workspace endpoints"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_workspace():
    """Get workspace data"""
    return {"status": "ok", "workspace": {}}
