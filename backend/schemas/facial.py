from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class FaceSearchBase(BaseModel):
    case_id: int
    search_type: str = Field(..., pattern="^(local|reverse)$")


class FaceSearchCreate(FaceSearchBase):
    image_base64: str  # Base64 encoded image


class FaceMatchBase(BaseModel):
    name: Optional[str] = None
    alias: Optional[str] = None
    notes: Optional[str] = None


class FaceMatchResponse(FaceMatchBase):
    id: int
    search_id: int
    matched_image_path: Optional[str] = None
    source_url: Optional[str] = None
    confidence_score: float

    class Config:
        from_attributes = True


class FaceSearchResponse(FaceSearchBase):
    id: int
    source_image_path: str
    timestamp: datetime
    matches: List[FaceMatchResponse] = []

    class Config:
        from_attributes = True


class ReverseImageSearchRequest(BaseModel):
    case_id: int
    image_base64: str
    engines: List[str] = ["google", "yandex", "bing"]
