from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class UsernameSearchBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)


class UsernameSearchCreate(UsernameSearchBase):
    case_id: int


class UsernameResultResponse(BaseModel):
    id: int
    search_id: int
    platform: str
    profile_url: Optional[str] = None
    is_available: bool
    registered_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsernameSearchResponse(UsernameSearchBase):
    id: int
    case_id: int
    searched_at: datetime
    results: List[UsernameResultResponse] = []

    class Config:
        from_attributes = True


class NumberEmailSearchBase(BaseModel):
    search_type: str = Field(..., pattern="^(phone|email)$")
    search_value: str


class NumberEmailSearchCreate(NumberEmailSearchBase):
    case_id: int


class NumberEmailResultResponse(BaseModel):
    id: int
    search_id: int
    result_type: str
    result_data: Optional[str] = None
    source: Optional[str] = None
    confidence: str

    class Config:
        from_attributes = True


class NumberEmailSearchResponse(NumberEmailSearchBase):
    id: int
    case_id: int
    searched_at: datetime
    credits_used: int
    results: List[NumberEmailResultResponse] = []

    class Config:
        from_attributes = True


class CreditTopUpRequest(BaseModel):
    user_id: int
    credits: int = Field(..., gt=0)
