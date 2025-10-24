from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.database.models import NumberEmailSearch, NumberEmailResult, User, Case, AuditLog
from backend.schemas.tracker import (
    NumberEmailSearchCreate, NumberEmailSearchResponse,
    CreditTopUpRequest
)
from backend.routers.auth import get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=NumberEmailSearchResponse, status_code=status.HTTP_201_CREATED)
async def search_number_email(
    search_data: NumberEmailSearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search phone number or email"""
    logger.info(f"[Tracker] User {current_user.username} searching {search_data.search_type}: {search_data.search_value}")
    
    # Verify case exists
    case = db.query(Case).filter(Case.id == search_data.case_id).first()
    if not case:
        logger.error(f"[Tracker] Case {search_data.case_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Check if user has enough credits
    # Base cost: 10 credits per search
    required_credits = 10
    if current_user.credits < required_credits:
        logger.warning(f"[Tracker] User {current_user.username} has insufficient credits ({current_user.credits} < {required_credits})")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Required: {required_credits}, Available: {current_user.credits}"
        )
    
    # Create search record
    new_search = NumberEmailSearch(
        case_id=search_data.case_id,
        search_type=search_data.search_type,
        search_value=search_data.search_value,
        searched_at=datetime.utcnow(),
        credits_used=required_credits
    )
    
    db.add(new_search)
    
    # Deduct credits
    old_credits = current_user.credits
    current_user.credits -= required_credits
    
    db.commit()
    db.refresh(new_search)
    
    logger.info(f"[Tracker] ✓ Search created successfully (ID: {new_search.id})")
    logger.info(f"[Tracker] Credits: {old_credits} → {current_user.credits} (-{required_credits})")
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Number/Email Search",
        module="Number/Email Tracker",
        details=f"Searched {search_data.search_type}: {search_data.search_value} for case {case.case_number} (Credits: {required_credits})"
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"[Tracker] Search queued - Results will be aggregated from multiple sources")
    
    return new_search


@router.get("/search/{search_id}", response_model=NumberEmailSearchResponse)
async def get_search_results(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get search results by ID"""
    logger.info(f"[Tracker] User {current_user.username} retrieving search {search_id}")
    
    search = db.query(NumberEmailSearch).filter(
        NumberEmailSearch.id == search_id
    ).first()
    
    if not search:
        logger.error(f"[Tracker] Search {search_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    
    logger.info(f"[Tracker] ✓ Retrieved search {search_id} ({search.search_type}: {search.search_value})")
    return search


@router.get("/case/{case_id}", response_model=List[NumberEmailSearchResponse])
async def get_case_searches(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all searches for a case"""
    logger.info(f"[Tracker] User {current_user.username} retrieving searches for case {case_id}")
    
    # Verify case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        logger.error(f"[Tracker] Case {case_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    searches = db.query(NumberEmailSearch).filter(
        NumberEmailSearch.case_id == case_id
    ).order_by(NumberEmailSearch.searched_at.desc()).all()
    
    logger.info(f"[Tracker] ✓ Retrieved {len(searches)} searches for case {case.case_number}")
    return searches


@router.get("/credits")
async def get_user_credits(
    current_user: User = Depends(get_current_user)
):
    """Get current user's credit balance"""
    logger.info(f"[Tracker] User {current_user.username} checking credit balance: {current_user.credits}")
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "credits": current_user.credits,
        "status": "active"
    }


@router.post("/credits/topup")
async def topup_credits(
    topup_request: CreditTopUpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Top up user credits (Admin only)"""
    logger.info(f"[Tracker] User {current_user.username} attempting to top up credits")
    
    # Check if current user is admin (role check should be added)
    # For now, any authenticated user can do this - add admin check in production
    
    # Verify target user exists
    user = db.query(User).filter(User.id == topup_request.user_id).first()
    if not user:
        logger.error(f"[Tracker] User ID {topup_request.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Add credits
    old_balance = user.credits
    user.credits += topup_request.credits
    new_balance = user.credits
    
    db.commit()
    
    logger.info(f"[Tracker] ✓ Credits topped up for {user.username}: {old_balance} → {new_balance} (+{topup_request.credits})")
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Credits Added",
        module="Number/Email Tracker",
        details=f"Added {topup_request.credits} credits to {user.username} (Old: {old_balance}, New: {new_balance})"
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "message": "Credits added successfully",
        "user": user.username,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "credits_added": topup_request.credits
    }
