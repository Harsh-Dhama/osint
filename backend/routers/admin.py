from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.database.models import User, AuditLog, Report, SystemConfig
from backend.schemas.admin import (
    AuditLogResponse, ReportResponse,
    BackupRequest, BackupResponse
)
from backend.schemas.user import UserResponse
from datetime import datetime
import shutil
import os

router = APIRouter()


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: int = None,
    module: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin only
):
    """Get audit logs (Admin only)"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if module:
        query = query.filter(AuditLog.module == module)
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/reports", response_model=List[ReportResponse])
async def get_all_reports(
    skip: int = 0,
    limit: int = 100,
    report_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)
):
    """Get all reports"""
    query = db.query(Report)
    
    if report_type:
        query = query.filter(Report.report_type == report_type)
    
    reports = query.order_by(Report.generated_at.desc()).offset(skip).limit(limit).all()
    return reports


@router.get("/users/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin only
):
    """Get user statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_count = db.query(User).filter(User.role == "admin").count()
    investigator_count = db.query(User).filter(User.role == "investigator").count()
    viewer_count = db.query(User).filter(User.role == "viewer").count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "roles": {
            "admin": admin_count,
            "investigator": investigator_count,
            "viewer": viewer_count
        }
    }


@router.get("/system/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin only
):
    """Get system statistics"""
    from backend.database.models import (
        Case, WhatsAppProfile, FaceSearch, SocialProfile,
        MonitoredKeyword, UsernameSearch, NumberEmailSearch
    )
    
    stats = {
        "cases": {
            "total": db.query(Case).count(),
            "open": db.query(Case).filter(Case.status == "open").count(),
            "in_progress": db.query(Case).filter(Case.status == "in_progress").count(),
            "closed": db.query(Case).filter(Case.status == "closed").count()
        },
        "modules": {
            "whatsapp_profiles": db.query(WhatsAppProfile).count(),
            "face_searches": db.query(FaceSearch).count(),
            "social_profiles": db.query(SocialProfile).count(),
            "monitored_keywords": db.query(MonitoredKeyword).count(),
            "username_searches": db.query(UsernameSearch).count(),
            "number_email_searches": db.query(NumberEmailSearch).count()
        },
        "reports": db.query(Report).count(),
        "audit_logs": db.query(AuditLog).count()
    }
    
    return stats


@router.post("/backup", response_model=BackupResponse)
async def create_backup(
    backup_request: BackupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin only
):
    """Create system backup (Admin only)"""
    try:
        # Create backup directory
        os.makedirs("backups", exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"osint_backup_{timestamp}"
        backup_path = f"backups/{backup_name}"
        
        os.makedirs(backup_path, exist_ok=True)
        
        # Backup database
        shutil.copy2("data/osint.db", f"{backup_path}/osint.db")
        
        # Backup reports if requested
        if backup_request.include_reports and os.path.exists("reports"):
            shutil.copytree("reports", f"{backup_path}/reports")
        
        # Backup media if requested
        if backup_request.include_media and os.path.exists("uploads"):
            shutil.copytree("uploads", f"{backup_path}/uploads")
        
        # Create archive
        shutil.make_archive(backup_path, 'zip', backup_path)
        
        # Remove temporary folder
        shutil.rmtree(backup_path)
        
        # Get backup size
        backup_file = f"{backup_path}.zip"
        size_mb = os.path.getsize(backup_file) / (1024 * 1024)
        
        # Log action
        audit_log = AuditLog(
            user_id=current_user.id,
            action="Backup Created",
            module="Admin",
            details=f"Created backup: {backup_name}.zip"
        )
        db.add(audit_log)
        db.commit()
        
        return BackupResponse(
            backup_file=f"{backup_name}.zip",
            size_mb=round(size_mb, 2),
            created_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}"
        )


@router.get("/config")
async def get_system_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin only
):
    """Get system configuration"""
    configs = db.query(SystemConfig).all()
    return {config.key: config.value for config in configs}


@router.post("/config")
async def update_system_config(
    key: str,
    value: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Admin only
):
    """Update system configuration"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    
    if config:
        config.value = value
        config.updated_at = datetime.utcnow()
    else:
        config = SystemConfig(key=key, value=value)
        db.add(config)
    
    db.commit()
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Config Updated",
        module="Admin",
        details=f"Updated config: {key}"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Configuration updated successfully"}
