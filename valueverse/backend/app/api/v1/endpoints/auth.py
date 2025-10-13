"""Authentication endpoints"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    # Mock authentication for demo
    if request.email == "admin@valueverse.ai" and request.password == "demo123":
        return TokenResponse(
            access_token="mock-jwt-token-for-demo",
            token_type="bearer"
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )
