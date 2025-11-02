from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database.database import get_db
from backend.database.models import User, UserRole
from backend.schemas.tracker import (
    TrackerSearchRequest, TrackerSearchResponse, ConsolidatedSearchResponse,
    CreditTopUpRequest, BulkCreditTopUp, CreditBalance, CreditTransactionResponse,
    TrackerStatsResponse, MODULE_CREDITS, TrackerModule
)
from backend.routers.auth import get_current_user
from backend.modules.tracker_service import TrackerService
from backend.utils.tracker_report_generator import generate_tracker_report
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# SEARCH ENDPOINTS
# ============================================

@router.post("/search", response_model=TrackerSearchResponse, status_code=status.HTTP_201_CREATED)
async def initiate_tracker_search(
    request: TrackerSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate a comprehensive tracker search across multiple modules
    
    - **case_id**: Case to associate search with
    - **search_type**: "phone" or "email"
    - **search_value**: Phone number or email address
    - **modules**: List of modules to query (truename, upi, aadhaar, etc.)
    - **accept_disclaimer**: Must be true for sensitive data lookups
    """
    logger.info(f"[Tracker] User {current_user.username} initiating search: {request.search_type} - {request.search_value}")
    logger.info(f"[Tracker] Modules requested: {[m.value for m in request.modules]}")
    
    service = TrackerService(db)
    
    # Calculate required credits
    credits_required = service.calculate_credits_required(request.modules)
    has_enough, current_balance = service.check_user_credits(current_user.id, credits_required)
    
    if not has_enough:
        logger.warning(f"[Tracker] Insufficient credits. Required: {credits_required}, Available: {current_balance}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. Required: {credits_required}, Available: {current_balance}"
        )
    
    # Create search
    search, error = await service.create_search(
        user_id=current_user.id,
        case_id=request.case_id,
        search_type=request.search_type,
        search_value=request.search_value,
        modules=request.modules
    )
    
    if not search:
        logger.error(f"[Tracker] Failed to create search: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Execute search in background
    background_tasks.add_task(
        service.execute_search,
        search.id,
        request.modules
    )
    
    logger.info(f"[Tracker] ✓ Search {search.id} created and queued for execution")
    
    return TrackerSearchResponse(
        search_id=search.id,
        status="pending",
        credits_required=credits_required,
        credits_available=current_balance,
        message=f"Search initiated. Querying {len(request.modules)} modules. Check back in 1-2 minutes."
    )


@router.get("/search/{search_id}", response_model=ConsolidatedSearchResponse)
async def get_tracker_search_results(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete results for a tracker search
    
    Returns consolidated data from all queried modules with cross-module insights
    """
    logger.info(f"[Tracker] User {current_user.username} retrieving search {search_id}")
    
    service = TrackerService(db)
    results = service.get_search_results(search_id)
    
    if not results:
        logger.error(f"[Tracker] Search {search_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    
    logger.info(f"[Tracker] ✓ Retrieved search {search_id} with {len(results['module_results'])} module results")
    
    return ConsolidatedSearchResponse(**results)


@router.get("/case/{case_id}/searches")
async def get_case_tracker_searches(
    case_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all tracker searches for a specific case"""
    from backend.database.models import NumberEmailSearch, Case
    
    logger.info(f"[Tracker] User {current_user.username} retrieving searches for case {case_id}")
    
    # Verify case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    searches = db.query(NumberEmailSearch).filter(
        NumberEmailSearch.case_id == case_id
    ).order_by(NumberEmailSearch.searched_at.desc()).limit(limit).all()
    
    logger.info(f"[Tracker] ✓ Retrieved {len(searches)} searches for case {case.case_number}")
    
    return {
        "case_id": case_id,
        "case_number": case.case_number,
        "total_searches": len(searches),
        "searches": [
            {
                "id": s.id,
                "search_type": s.search_type,
                "search_value": s.search_value,
                "status": s.status,
                "credits_used": s.credits_used,
                "searched_at": s.searched_at.isoformat(),
                "modules": s.modules_requested.split(',') if s.modules_requested else []
            }
            for s in searches
        ]
    }


@router.get("/recent")
async def get_recent_searches(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's recent tracker searches"""
    from backend.database.models import NumberEmailSearch
    
    searches = db.query(NumberEmailSearch).filter(
        NumberEmailSearch.user_id == current_user.id
    ).order_by(NumberEmailSearch.searched_at.desc()).limit(limit).all()
    
    return {
        "total": len(searches),
        "searches": [
            {
                "id": s.id,
                "search_type": s.search_type,
                "search_value": s.search_value,
                "case_id": s.case_id,
                "status": s.status,
                "credits_used": s.credits_used,
                "searched_at": s.searched_at.isoformat()
            }
            for s in searches
        ]
    }


# ============================================
# CREDIT MANAGEMENT ENDPOINTS
# ============================================

@router.get("/credits/balance", response_model=CreditBalance)
async def get_credit_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's credit balance and statistics"""
    logger.info(f"[Tracker] User {current_user.username} checking credit balance")
    
    service = TrackerService(db)
    history = service.get_user_credit_history(current_user.id, limit=1000)
    
    total_earned = sum(t['amount'] for t in history if t['type'] == 'credit')
    total_spent = sum(t['amount'] for t in history if t['type'] == 'debit')
    
    return CreditBalance(
        user_id=current_user.id,
        username=current_user.username,
        current_balance=current_user.credits,
        total_earned=total_earned,
        total_spent=total_spent
    )


@router.get("/credits/history", response_model=List[CreditTransactionResponse])
async def get_credit_transaction_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's credit transaction history"""
    logger.info(f"[Tracker] User {current_user.username} retrieving credit history")
    
    service = TrackerService(db)
    history = service.get_user_credit_history(current_user.id, limit=limit)
    
    return [CreditTransactionResponse(**t) for t in history]


@router.post("/credits/topup", status_code=status.HTTP_200_OK)
async def topup_user_credits(
    request: CreditTopUpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Top up credits for a user (Admin only)
    
    Requires admin role to add credits to any user account
    """
    logger.info(f"[Tracker] Admin {current_user.username} attempting credit top-up")
    
    # Check admin permission
    if current_user.role != UserRole.ADMIN:
        logger.warning(f"[Tracker] Non-admin user {current_user.username} attempted credit top-up")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can top up credits"
        )
    
    service = TrackerService(db)
    success = service.add_credits(
        user_id=request.user_id,
        amount=request.credits,
        admin_id=current_user.id,
        description=request.description
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add credits. User may not exist."
        )
    
    # Get updated user
    target_user = db.query(User).filter(User.id == request.user_id).first()
    
    logger.info(f"[Tracker] ✓ Added {request.credits} credits to user {target_user.username}")
    
    return {
        "success": True,
        "message": f"Successfully added {request.credits} credits",
        "user_id": target_user.id,
        "username": target_user.username,
        "new_balance": target_user.credits
    }


@router.post("/credits/bulk-topup", status_code=status.HTTP_200_OK)
async def bulk_topup_credits(
    request: BulkCreditTopUp,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Top up credits for multiple users (Admin only)
    
    Useful for monthly credit allocations
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform bulk credit top-ups"
        )
    
    service = TrackerService(db)
    results = []
    
    for user_id in request.user_ids:
        success = service.add_credits(
            user_id=user_id,
            amount=request.credits_per_user,
            admin_id=current_user.id,
            description=request.description or "Bulk credit top-up"
        )
        
        user = db.query(User).filter(User.id == user_id).first()
        results.append({
            "user_id": user_id,
            "username": user.username if user else "Unknown",
            "success": success,
            "new_balance": user.credits if user else 0
        })
    
    successful = sum(1 for r in results if r['success'])
    
    logger.info(f"[Tracker] ✓ Bulk top-up completed: {successful}/{len(request.user_ids)} successful")
    
    return {
        "message": f"Bulk top-up completed: {successful}/{len(request.user_ids)} successful",
        "credits_per_user": request.credits_per_user,
        "results": results
    }


# ============================================
# STATISTICS & ANALYTICS
# ============================================

@router.get("/stats", response_model=TrackerStatsResponse)
async def get_tracker_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tracker module usage statistics for current user
    
    Shows search counts, credit usage, success rates, and trends
    """
    logger.info(f"[Tracker] User {current_user.username} retrieving tracker statistics")
    
    service = TrackerService(db)
    stats = service.get_tracker_stats(user_id=current_user.id)
    
    return TrackerStatsResponse(**stats)


@router.get("/admin/stats")
async def get_global_tracker_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get global tracker statistics (Admin only)
    
    Shows platform-wide usage metrics
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view global statistics"
        )
    
    logger.info(f"[Tracker] Admin {current_user.username} retrieving global statistics")
    
    service = TrackerService(db)
    stats = service.get_tracker_stats(user_id=None)  # Global stats
    
    # Add credit statistics
    from backend.database.models import CreditTransaction
    
    total_credits_issued = db.query(CreditTransaction).filter(
        CreditTransaction.transaction_type == "credit"
    ).count()
    
    total_credits_spent = db.query(CreditTransaction).filter(
        CreditTransaction.transaction_type == "debit"
    ).count()
    
    stats['credits'] = {
        'total_issued': total_credits_issued,
        'total_spent': total_credits_spent
    }
    
    return stats


# ============================================
# MODULE INFORMATION
# ============================================

@router.get("/modules")
async def get_available_modules():
    """
    Get list of available tracker modules with credit costs
    
    Returns module names, descriptions, and credit requirements
    """
    modules = [
        {
            "name": TrackerModule.TRUE_NAME.value,
            "display_name": "True Name & Address",
            "description": "Get registered name and address for phone number",
            "credits": MODULE_CREDITS[TrackerModule.TRUE_NAME],
            "sensitive": False
        },
        {
            "name": TrackerModule.SOCIAL_MEDIA.value,
            "display_name": "Social Media Presence",
            "description": "Find social media profiles linked to phone/email",
            "credits": MODULE_CREDITS[TrackerModule.SOCIAL_MEDIA],
            "sensitive": False
        },
        {
            "name": TrackerModule.UPI_ID.value,
            "display_name": "UPI ID Lookup",
            "description": "Get UPI IDs associated with phone number",
            "credits": MODULE_CREDITS[TrackerModule.UPI_ID],
            "sensitive": True
        },
        {
            "name": TrackerModule.VEHICLE.value,
            "display_name": "Vehicle Details",
            "description": "Find registered vehicles linked to phone number",
            "credits": MODULE_CREDITS[TrackerModule.VEHICLE],
            "sensitive": True
        },
        {
            "name": TrackerModule.AADHAAR.value,
            "display_name": "Aadhaar Verification",
            "description": "Check Aadhaar linkage (Requires disclaimer acceptance)",
            "credits": MODULE_CREDITS[TrackerModule.AADHAAR],
            "sensitive": True,
            "disclaimer_required": True
        },
        {
            "name": TrackerModule.DEEP_SEARCH.value,
            "display_name": "Deep Search / Data Breaches",
            "description": "Search for leaked information and data breaches",
            "credits": MODULE_CREDITS[TrackerModule.DEEP_SEARCH],
            "sensitive": True
        },
        {
            "name": TrackerModule.LINKED_EMAILS.value,
            "display_name": "Linked Email Addresses",
            "description": "Find email addresses associated with phone/email",
            "credits": MODULE_CREDITS[TrackerModule.LINKED_EMAILS],
            "sensitive": False
        },
        {
            "name": TrackerModule.ALTERNATE_NUMBERS.value,
            "display_name": "Alternate Phone Numbers",
            "description": "Find other phone numbers linked to same person",
            "credits": MODULE_CREDITS[TrackerModule.ALTERNATE_NUMBERS],
            "sensitive": False
        },
        {
            "name": TrackerModule.BANK_DETAILS.value,
            "display_name": "Bank Account Details",
            "description": "Get bank account information (Requires authorization)",
            "credits": MODULE_CREDITS[TrackerModule.BANK_DETAILS],
            "sensitive": True,
            "disclaimer_required": True
        }
    ]
    
    return {
        "total_modules": len(modules),
        "modules": modules,
        "note": "Sensitive modules require disclaimer acceptance and higher credits"
    }


@router.get("/disclaimer")
async def get_tracker_disclaimer():
    """
    Get the mandatory disclaimer for sensitive data lookups
    
    Must be shown to users before querying Aadhaar, bank details, etc.
    """
    return {
        "title": "Sensitive Data Lookup - Legal Disclaimer",
        "content": """
        ⚠️ IMPORTANT LEGAL NOTICE ⚠️
        
        You are about to access SENSITIVE PERSONAL INFORMATION protected under:
        - The Information Technology Act, 2000
        - The Aadhaar Act, 2016
        - The Personal Data Protection Act
        
        This tool is EXCLUSIVELY for law enforcement investigations and must only be used:
        1. With proper legal authorization
        2. For legitimate investigative purposes
        3. In compliance with court orders or statutory provisions
        
        UNAUTHORIZED ACCESS OR MISUSE:
        - Constitutes a criminal offense
        - May result in prosecution and imprisonment
        - Violates citizens' fundamental right to privacy
        
        By proceeding, you certify that:
        ✓ You have lawful authority to access this information
        ✓ The search is part of an active investigation
        ✓ You will handle the data with utmost confidentiality
        ✓ You understand the legal consequences of misuse
        
        All activities are logged and audited.
        """,
        "acceptance_required": True,
        "applicable_modules": [
            TrackerModule.AADHAAR.value,
            TrackerModule.BANK_DETAILS.value,
            TrackerModule.VEHICLE.value
        ]
    }


# ============================================
# REPORT GENERATION
# ============================================

@router.get("/search/{search_id}/export/pdf")
async def export_tracker_report_pdf(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and download PDF report for tracker search
    
    Creates a professional PDF report with:
    - Case and officer information
    - Complete search results
    - Module-by-module breakdown
    - Cross-module insights
    - Legal disclaimers
    - QR code for verification
    """
    logger.info(f"[Tracker] User {current_user.username} requesting PDF export for search {search_id}")
    
    # Verify search exists
    from backend.database.models import NumberEmailSearch
    
    search = db.query(NumberEmailSearch).filter(
        NumberEmailSearch.id == search_id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    
    # Generate PDF report
    try:
        pdf_path = generate_tracker_report(search_id)
        
        if not pdf_path or not Path(pdf_path).exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate PDF report"
            )
        
        logger.info(f"[Tracker] ✓ PDF report generated: {pdf_path}")
        
        # Return file for download
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=Path(pdf_path).name,
            headers={
                "Content-Disposition": f"attachment; filename={Path(pdf_path).name}"
            }
        )
        
    except Exception as e:
        logger.error(f"[Tracker] Failed to export PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(e)}"
        )
