from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class APIKeyCreate(BaseModel):
    name: str
    project_id: Optional[str] = None
    expires_in_days: Optional[int] = 365


class APIKeyResponse(BaseModel):
    id: str
    name: str
    api_key: str
    project_id: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    last_used: Optional[datetime] = None


class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserPreferences(BaseModel):
    theme: str = "dark"
    language: str = "en"
    notifications_enabled: bool = True
    email_notifications: bool = True


class UserStats(BaseModel):
    total_projects: int
    total_deployments: int
    total_commits: int
    total_storage_used: int
    last_login: Optional[datetime] = None
