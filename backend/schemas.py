from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserStatsResponse(BaseModel):
    total_tests: int
    best_wpm: float
    avg_wpm: float
    avg_accuracy: float
    total_xp: int

    class Config:
        from_attributes = True

class ForgotPassword(BaseModel):
    email: str

class ResetPassword(BaseModel):
    token: str
    new_password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    stats: Optional[UserStatsResponse] = None
    level: Optional[int] = None

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    username: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None

# Test Result Schemas
class TestResultCreate(BaseModel):
    wpm: float
    raw_wpm: float
    accuracy: float
    mode: str
    duration: int
