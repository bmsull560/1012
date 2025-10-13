# backend/app/schemas/user.py

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    """Base schema for user"""
    username: str
    email: EmailStr

    model_config = ConfigDict(str_strip_whitespace=True)

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(not char.isalnum() for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

class User(UserBase):
    """Schema for user"""
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """Schema for token"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token data"""
    username: Optional[str] = None
