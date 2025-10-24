from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.database.models import MonitoredKeyword, MonitoredPost, User, Case, AuditLog
from backend.schemas.social import (
    MonitoredKeywordCreate, MonitoredKeywordResponse,
    MonitoredPostResponse
)
from datetime import datetime

router = APIRouter()


@router.post("/keywords", response_model=MonitoredKeywordResponse, status_code=status.HTTP_201_CREATED)
async def create_monitored_keyword(
    keyword_data: MonitoredKeywordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Create a new monitored keyword"""
    # Verify case exists
    case = db.query(Case).filter(Case.id == keyword_data.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    new_keyword = MonitoredKeyword(
        case_id=keyword_data.case_id,
        keyword=keyword_data.keyword,
        location=keyword_data.location,
        platforms=keyword_data.platforms,
        created_at=datetime.utcnow()
    )
    
    db.add(new_keyword)
    db.commit()
    db.refresh(new_keyword)
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Keyword Monitoring Started",
        module="Social Media Monitoring",
        details=f"Monitoring keyword: {keyword_data.keyword}"
    )
    db.add(audit_log)
    db.commit()
    
    return new_keyword


@router.post("/keywords/{keyword_id}/monitor")
async def monitor_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Trigger monitoring for a keyword"""
    keyword = db.query(MonitoredKeyword).filter(MonitoredKeyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    
    # TODO: Implement actual monitoring logic here
    # This would scrape posts and perform sentiment analysis
    
    keyword.last_monitored = datetime.utcnow()
    db.commit()
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Keyword Monitored",
        module="Social Media Monitoring",
        details=f"Monitored keyword: {keyword.keyword}"
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "message": "Monitoring completed",
        "keyword": keyword.keyword,
        "last_monitored": keyword.last_monitored
    }


@router.get("/keywords/case/{case_id}", response_model=List[MonitoredKeywordResponse])
async def get_case_keywords(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get all monitored keywords for a case"""
    keywords = db.query(MonitoredKeyword).filter(
        MonitoredKeyword.case_id == case_id
    ).all()
    return keywords


@router.get("/keywords/{keyword_id}", response_model=MonitoredKeywordResponse)
async def get_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get monitored keyword by ID"""
    keyword = db.query(MonitoredKeyword).filter(
        MonitoredKeyword.id == keyword_id
    ).first()
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    return keyword


@router.get("/posts/{keyword_id}", response_model=List[MonitoredPostResponse])
async def get_keyword_posts(
    keyword_id: int,
    sentiment: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get all posts for a monitored keyword"""
    query = db.query(MonitoredPost).filter(MonitoredPost.keyword_id == keyword_id)
    
    if sentiment:
        query = query.filter(MonitoredPost.sentiment == sentiment)
    
    posts = query.all()
    return posts


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Delete monitored keyword"""
    keyword = db.query(MonitoredKeyword).filter(
        MonitoredKeyword.id == keyword_id
    ).first()
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Keyword Monitoring Stopped",
        module="Social Media Monitoring",
        details=f"Stopped monitoring: {keyword.keyword}"
    )
    db.add(audit_log)
    
    db.delete(keyword)
    db.commit()
    
    return {"message": "Keyword monitoring stopped"}
