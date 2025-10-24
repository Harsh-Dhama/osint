from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
    VIEWER = "viewer"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    # Use plain str for email in responses to allow local/testing addresses
    email: str
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.INVESTIGATOR
    badge_number: Optional[str] = None
    department: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    badge_number: Optional[str] = None
    department: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    credits: Optional[int] = None


class UserResponse(UserBase):
    id: int
    credits: int
    is_active: bool
    disclaimer_accepted: bool
    disclaimer_accepted_at: Optional[datetime] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class DisclaimerAcceptance(BaseModel):
    accepted: bool = True


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
