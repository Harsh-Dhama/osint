from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.database.models import UsernameSearch, UsernameResult, User, Case, AuditLog
from backend.schemas.tracker import UsernameSearchCreate, UsernameSearchResponse
from datetime import datetime

router = APIRouter()


@router.post("/search", response_model=UsernameSearchResponse, status_code=status.HTTP_201_CREATED)
async def search_username(
    search_data: UsernameSearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Search for username across platforms"""
    # Verify case exists
    case = db.query(Case).filter(Case.id == search_data.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Create search record
    new_search = UsernameSearch(
        case_id=search_data.case_id,
        username=search_data.username,
        searched_at=datetime.utcnow()
    )
    
    db.add(new_search)
    db.commit()
    db.refresh(new_search)
    
    # TODO: Implement actual username search using Sherlock/Maigret
    # Placeholder - will be implemented in modules/username_searcher.py
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Username Search",
        module="Username Searcher",
        details=f"Searched username: {search_data.username}"
    )
    db.add(audit_log)
    db.commit()
    
    return new_search


@router.get("/search/{search_id}", response_model=UsernameSearchResponse)
async def get_username_search(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get username search results by ID"""
    search = db.query(UsernameSearch).filter(UsernameSearch.id == search_id).first()
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    return search


@router.get("/case/{case_id}", response_model=List[UsernameSearchResponse])
async def get_case_username_searches(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get all username searches for a case"""
    searches = db.query(UsernameSearch).filter(
        UsernameSearch.case_id == case_id
    ).all()
    return searches
