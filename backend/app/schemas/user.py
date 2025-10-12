# backend/app/schemas/user.py

from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class UserBase(BaseModel):
    """Base schema for user"""
    username: str
    email: EmailStr

    class Config:
        """Config for UserBase"""
        anystr_strip_whitespace = True

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str

    @validator('password')
    def password_must_contain_uppercase(cls, v):
        """Validate password to contain at least one uppercase letter"""
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

    @validator('password')
    def password_must_contain_lowercase(cls, v):
        """Validate password to contain at least one lowercase letter"""
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

    @validator('password')
    def password_must_contain_number(cls, v):
        """Validate password to contain at least one number"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        return v

    @validator('password')
    def password_must_contain_special_char(cls, v):
        """Validate password to contain at least one special character"""
        if not any(not char.isalnum() for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('password')
    def password_must_be_at_least_8_chars(cls, v):
        """Validate password to be at least 8 characters long"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class User(UserBase):
    """Schema for user"""
    id: int
    is_active: bool

    class Config:
        """Config for User"""
        orm_mode = True

class Token(BaseModel):
    """Schema for token"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token data"""
    username: Optional[str] = None
