from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SocialProfileBase(BaseModel):
    platform: str = Field(..., pattern="^(twitter|facebook|instagram)$")
    username: str = Field(..., min_length=1, max_length=100)


class SocialProfileCreate(SocialProfileBase):
    case_id: int


class SocialBulkUpload(BaseModel):
    case_id: int
    platform: str
    usernames: List[str]


class SocialProfileResponse(SocialProfileBase):
    id: int
    case_id: int
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers_count: int
    following_count: int
    posts_count: int
    profile_picture_path: Optional[str] = None
    profile_url: Optional[str] = None
    scraped_at: datetime

    class Config:
        from_attributes = True


class MonitoredKeywordBase(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = None
    platforms: Optional[str] = None


class MonitoredKeywordCreate(MonitoredKeywordBase):
    case_id: int


class MonitoredPostResponse(BaseModel):
    id: int
    keyword_id: int
    platform: str
    post_url: Optional[str] = None
    post_text: Optional[str] = None
    author: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    location: Optional[str] = None
    posted_at: Optional[datetime] = None
    scraped_at: datetime

    class Config:
        from_attributes = True


class MonitoredKeywordResponse(MonitoredKeywordBase):
    id: int
    case_id: int
    created_at: datetime
    last_monitored: Optional[datetime] = None
    results: List[MonitoredPostResponse] = []

    class Config:
        from_attributes = True
