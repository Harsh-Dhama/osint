from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
from backend.database.database import get_db
from backend.database.models import UsernameSearch, UsernameResult, User, Case, AuditLog
from backend.schemas.tracker import (
    UsernameSearchCreate, 
    UsernameSearchResponse,
    UsernameResultResponse
)
from backend.modules.username_searcher import username_searcher_service
from backend.utils.username_report_generator import generate_username_report
from backend.routers.auth import get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=UsernameSearchResponse, status_code=status.HTTP_201_CREATED)
async def search_username(
    search_data: UsernameSearchCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for username across 40+ social media platforms and online services.
    
    This endpoint initiates a username search across multiple platforms including:
    - Social Media: Instagram, Twitter, Facebook, TikTok, LinkedIn, etc.
    - Developer Platforms: GitHub, GitLab, Stack Overflow, etc.
    - Content Platforms: YouTube, Twitch, Medium, etc.
    - Gaming: Steam, Xbox, PlayStation, Discord, etc.
    
    Results are cached for 7 days to avoid redundant queries.
    """
    
    # Validate username format
    if not search_data.username or len(search_data.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    # Verify case exists if provided
    if search_data.case_id:
        case = db.query(Case).filter(Case.id == search_data.case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
    
    try:
        logger.info(f"Initiating username search for: {search_data.username}")
        
        # Perform username search using the service
        search = await username_searcher_service.search_username(
            username=search_data.username,
            case_id=search_data.case_id,
            officer_name=search_data.officer_name or current_user.username,
            db=db,
            use_cache=True
        )
        
        # Log action
        audit_log = AuditLog(
            user_id=current_user.id,
            action="Username Search",
            module="Username Searcher",
            details=f"Searched username: {search_data.username} - Found on {search.platforms_found} platforms"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Username search completed: {search_data.username} - Found on {search.platforms_found}/{search.platforms_checked} platforms")
        
        return search
        
    except Exception as e:
        logger.error(f"Username search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Username search failed: {str(e)}"
        )


@router.get("/search/{search_id}", response_model=UsernameSearchResponse)
async def get_username_search(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get username search results by ID with all platform results"""
    search = db.query(UsernameSearch).filter(UsernameSearch.id == search_id).first()
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    return search


@router.get("/search/{search_id}/results", response_model=List[UsernameResultResponse])
async def get_username_results(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed platform results for a username search"""
    # Verify search exists
    search = db.query(UsernameSearch).filter(UsernameSearch.id == search_id).first()
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    
    # Get all results
    results = db.query(UsernameResult).filter(
        UsernameResult.search_id == search_id
    ).order_by(UsernameResult.confidence_score.desc()).all()
    
    return results


@router.get("/case/{case_id}", response_model=List[UsernameSearchResponse])
async def get_case_username_searches(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all username searches for a case"""
    searches = db.query(UsernameSearch).filter(
        UsernameSearch.case_id == case_id
    ).order_by(UsernameSearch.searched_at.desc()).all()
    return searches


@router.delete("/cache/clear", status_code=status.HTTP_200_OK)
async def clear_username_cache(
    username: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear cached username searches.
    
    Args:
        username: Optional specific username to clear (if None, clears all cache)
    
    Requires admin privileges to clear all cache.
    """
    
    # Check if admin when clearing all cache
    if not username and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to clear all cache"
        )
    
    try:
        count = username_searcher_service.clear_cache(username, db)
        
        # Log action
        audit_log = AuditLog(
            user_id=current_user.id,
            action="Clear Username Cache",
            module="Username Searcher",
            details=f"Cleared {count} cached searches" + (f" for username: {username}" if username else " (all)")
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "message": f"Successfully cleared {count} cached searches",
            "username": username,
            "count": count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get username search cache statistics"""
    try:
        stats = username_searcher_service.get_cache_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.get("/search/{search_id}/export/pdf")
async def export_username_report_pdf(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export username search results as a professional PDF report.
    
    The report includes:
    - Search metadata (username, date, case info, officer)
    - Results summary with statistics
    - Detailed platform results with confidence scores
    - Platform URLs and discovery dates
    - QR code for report verification
    - Legal disclaimers and compliance information
    """
    
    # Verify search exists
    search = db.query(UsernameSearch).filter(UsernameSearch.id == search_id).first()
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Username search {search_id} not found"
        )
    
    try:
        logger.info(f"Generating PDF report for username search {search_id}")
        
        # Generate PDF report
        pdf_path = generate_username_report(search_id, db)
        
        # Verify file was created
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not generated: {pdf_path}")
        
        # Log action
        audit_log = AuditLog(
            user_id=current_user.id,
            action="Export Username Report",
            module="Username Searcher",
            details=f"Exported PDF report for search {search_id} (username: {search.username})"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"PDF report generated successfully: {pdf_path}")
        
        # Return file
        return FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename=f"username_report_{search_id}.pdf",
            headers={
                "Content-Disposition": f"attachment; filename=username_report_{search_id}.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(e)}"
        )

