from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserAuth(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    created_at: datetime
    project_count: Optional[int] = 0
    total_deployments: Optional[int] = 0


class SupabaseUser(BaseModel):
    """Model for Supabase auth user"""
    id: str
    email: str
    username: Optional[str] = None
    created_at: datetime


class UserSession(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    user: SupabaseUser
