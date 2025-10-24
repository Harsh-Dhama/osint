from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.database.models import SocialProfile, User, Case, AuditLog
from backend.schemas.social import (
    SocialProfileCreate, SocialProfileResponse,
    SocialBulkUpload
)
from datetime import datetime

router = APIRouter()


@router.post("/scrape", response_model=SocialProfileResponse, status_code=status.HTTP_201_CREATED)
async def scrape_social_profile(
    profile_data: SocialProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Scrape single social media profile"""
    # Verify case exists
    case = db.query(Case).filter(Case.id == profile_data.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # TODO: Implement actual social media scraping logic
    
    new_profile = SocialProfile(
        case_id=profile_data.case_id,
        platform=profile_data.platform,
        username=profile_data.username,
        scraped_at=datetime.utcnow()
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Social Profile Scraped",
        module="Social Media Scraper",
        details=f"Scraped {profile_data.platform} profile: {profile_data.username}"
    )
    db.add(audit_log)
    db.commit()
    
    return new_profile


@router.post("/scrape/bulk")
async def scrape_bulk_social(
    bulk_data: SocialBulkUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Scrape multiple social media profiles"""
    # Verify case exists
    case = db.query(Case).filter(Case.id == bulk_data.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    profiles_added = []
    
    for username in bulk_data.usernames:
        # TODO: Implement actual scraping logic
        profile = SocialProfile(
            case_id=bulk_data.case_id,
            platform=bulk_data.platform,
            username=username,
            scraped_at=datetime.utcnow()
        )
        db.add(profile)
        profiles_added.append(username)
    
    db.commit()
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Bulk Social Scrape",
        module="Social Media Scraper",
        details=f"Scraped {len(profiles_added)} {bulk_data.platform} profiles"
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "message": f"Successfully queued {len(profiles_added)} profiles for scraping",
        "profiles": profiles_added
    }


@router.get("/case/{case_id}", response_model=List[SocialProfileResponse])
async def get_case_social_profiles(
    case_id: int,
    platform: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get all social profiles for a case"""
    query = db.query(SocialProfile).filter(SocialProfile.case_id == case_id)
    
    if platform:
        query = query.filter(SocialProfile.platform == platform)
    
    profiles = query.all()
    return profiles


@router.get("/{profile_id}", response_model=SocialProfileResponse)
async def get_social_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get social profile by ID"""
    profile = db.query(SocialProfile).filter(SocialProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile
