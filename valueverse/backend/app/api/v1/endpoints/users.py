"""User management endpoints"""

from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/")
async def list_users():
    """List all users"""
    return []

@router.get("/me")
async def get_current_user():
    """Get current user"""
    return {
        "id": "1",
        "email": "admin@valueverse.ai",
        "name": "Admin User",
        "role": "admin"
    }
