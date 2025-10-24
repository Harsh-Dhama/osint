from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.database.models import User, AuditLog
from backend.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.auth.security import get_password_hash

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin check will be added
):
    """Get all users (Admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin or self check
):
    """Update user information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="User Updated",
        module="User Management",
        details=f"Updated user: {user.username}"
    )
    db.add(audit_log)
    db.commit()
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin only
):
    """Deactivate user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Deactivate instead of deleting
    user.is_active = False
    db.commit()
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="User Deactivated",
        module="User Management",
        details=f"Deactivated user: {user.username}"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "User deactivated successfully"}
