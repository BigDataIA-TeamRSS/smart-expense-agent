"""User-related Pydantic schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    username: str
    email: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    monthly_income: Optional[float] = None
    life_stage: Optional[str] = None
    dependents: Optional[int] = None
    location: Optional[str] = None
    budget_alert_threshold: float = 1.30
    profile_completed: bool = False
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    monthly_income: Optional[float] = None
    life_stage: Optional[str] = None
    dependents: Optional[int] = None
    location: Optional[str] = None


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences"""
    budget_alert_threshold: Optional[float] = Field(None, ge=1.0, le=2.0)


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
