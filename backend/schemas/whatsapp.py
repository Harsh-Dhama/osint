from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WhatsAppProfileBase(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")


class WhatsAppProfileCreate(WhatsAppProfileBase):
    case_id: int


class WhatsAppBulkUpload(BaseModel):
    case_id: int
    phone_numbers: List[str]


class WhatsAppProfileResponse(WhatsAppProfileBase):
    id: int
    case_id: int
    display_name: Optional[str] = None
    about: Optional[str] = None
    profile_picture_path: Optional[str] = None
    last_seen: Optional[str] = None
    is_available: bool
    scraped_at: datetime

    class Config:
        from_attributes = True


class WhatsAppExportRequest(BaseModel):
    case_id: int
    format: str = Field(default="pdf", pattern="^(pdf|excel)$")
