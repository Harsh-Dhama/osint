from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.database.models import Case, User, AuditLog
from backend.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseAssignment
from backend.routers.auth import get_current_user
from datetime import datetime
import random
import string
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def generate_case_number() -> str:
    """Generate unique case number"""
    year = datetime.now().year
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"CASE-{year}-{random_part}"


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new case"""
    logger.info(f"[Cases] User {current_user.username} creating new case: {case_data.title}")
    
    # Generate unique case number
    case_number = generate_case_number()
    while db.query(Case).filter(Case.case_number == case_number).first():
        case_number = generate_case_number()
    
    new_case = Case(
        case_number=case_number,
        title=case_data.title,
        description=case_data.description,
        priority=case_data.priority,
        created_by=current_user.id,
        status="open"
    )
    
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    
    logger.info(f"[Cases] ✓ Case created: {case_number}")
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Case Created",
        module="Case Management",
        details=f"Created case: {case_number}"
    )
    db.add(audit_log)
    db.commit()
    
    return new_case


@router.get("/", response_model=List[CaseResponse])
async def get_all_cases(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all cases"""
    logger.info(f"[Cases] User {current_user.username} fetching cases")
    
    query = db.query(Case)
    
    if status:
        query = query.filter(Case.status == status)
    
    # If not admin, show only assigned or created cases
    # This check will be implemented with proper role checking
    
    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()
    logger.info(f"[Cases] ✓ Found {len(cases)} cases")
    return cases


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get case by ID"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update case information"""
    logger.info(f"[Cases] User {current_user.username} updating case {case_id}")
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Update fields if provided
    update_data = case_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    # If status changed to closed, set closed_at
    if case_data.status == "closed" and not case.closed_at:
        case.closed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(case)
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Case Updated",
        module="Case Management",
        details=f"Updated case: {case.case_number}"
    )
    db.add(audit_log)
    db.commit()
    
    return case


@router.post("/assign", status_code=status.HTTP_200_OK)
async def assign_case(
    assignment: CaseAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign case to user"""
    logger.info(f"[Cases] Admin {current_user.username} assigning case")
    
    case = db.query(Case).filter(Case.id == assignment.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    user = db.query(User).filter(User.id == assignment.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    case.assigned_to = assignment.user_id
    case.status = "in_progress"
    db.commit()
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Case Assigned",
        module="Case Management",
        details=f"Assigned case {case.case_number} to {user.username}"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Case assigned successfully"}


@router.delete("/{case_id}")
async def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete case (Admin only)"""
    logger.info(f"[Cases] Admin {current_user.username} deleting case {case_id}")
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Log action before deletion
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Case Deleted",
        module="Case Management",
        details=f"Deleted case: {case.case_number}"
    )
    db.add(audit_log)
    
    db.delete(case)
    db.commit()
    
    return {"message": "Case deleted successfully"}
