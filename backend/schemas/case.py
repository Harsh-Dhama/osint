from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(open|in_progress|closed)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    assigned_to: Optional[int] = None


class CaseResponse(CaseBase):
    id: int
    case_number: str
    status: str
    created_by: int
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CaseAssignment(BaseModel):
    case_id: int
    user_id: int
