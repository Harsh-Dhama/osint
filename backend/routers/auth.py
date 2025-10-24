from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User, AuditLog
from backend.schemas.user import (
    UserCreate, UserResponse, LoginRequest, Token,
    DisclaimerAcceptance, PasswordChange
)
from backend.auth.security import (
    verify_password, get_password_hash, create_access_token
)
from datetime import datetime, timedelta
import os

# OAuth2 scheme for protected endpoints in this router
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Decode access token and return the current user or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = None
    try:
        payload = __import__('backend.auth.security', fromlist=['decode_access_token']).decode_access_token(token)
    except Exception:
        payload = None

    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user (Admin only in production)"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        badge_number=user_data.badge_number,
        department=user_data.department,
        credits=int(os.getenv("DEFAULT_USER_CREDITS", 100))
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log action
    audit_log = AuditLog(
        user_id=new_user.id,
        action="User Registration",
        module="Authentication",
        details=f"New user registered: {user_data.username}"
    )
    db.add(audit_log)
    db.commit()
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480)))
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Log action
    audit_log = AuditLog(
        user_id=user.id,
        action="User Login",
        module="Authentication",
        details=f"User {user.username} logged in"
    )
    db.add(audit_log)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/accept-disclaimer")
async def accept_disclaimer(
    acceptance: DisclaimerAcceptance,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept mandatory disclaimer"""
    if not acceptance.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disclaimer must be accepted to use the platform"
        )
    
    current_user.disclaimer_accepted = True
    current_user.disclaimer_accepted_at = datetime.utcnow()
    db.commit()
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Disclaimer Accepted",
        module="Authentication",
        details="User accepted platform disclaimer"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Disclaimer accepted successfully"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Password Changed",
        module="Authentication",
        details="User changed password"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user
