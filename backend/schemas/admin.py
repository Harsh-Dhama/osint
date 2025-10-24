from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AuditLogBase(BaseModel):
    action: str
    module: str
    details: Optional[str] = None
    ip_address: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    user_id: int


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    report_type: str = Field(..., pattern="^(whatsapp|facial|social|monitoring|username|tracker|case)$")
    title: str


class ReportCreate(ReportBase):
    case_id: int
    generated_by: int


class ReportResponse(ReportBase):
    id: int
    case_id: int
    file_path: str
    generated_by: int
    generated_at: datetime

    class Config:
        from_attributes = True


class BackupRequest(BaseModel):
    include_reports: bool = True
    include_media: bool = True


class BackupResponse(BaseModel):
    backup_file: str
    size_mb: float
    created_at: datetime
