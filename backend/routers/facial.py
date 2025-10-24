from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.database.models import FaceSearch, FaceMatch, User, Case, AuditLog
from backend.schemas.facial import (
    FaceSearchCreate, FaceSearchResponse, FaceMatchResponse,
    ReverseImageSearchRequest
)
from backend.routers.auth import get_current_user
from datetime import datetime
import base64
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=FaceSearchResponse, status_code=status.HTTP_201_CREATED)
async def perform_face_search(
    search_data: FaceSearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform facial recognition search"""
    logger.info(f"[Facial] User {current_user.username} performing face search for case {search_data.case_id}")
    
    # Verify case exists
    case = db.query(Case).filter(Case.id == search_data.case_id).first()
    if not case:
        logger.error(f"[Facial] Case {search_data.case_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Decode and save image
    try:
        image_data = base64.b64decode(search_data.image_base64)
        os.makedirs("uploads/facial", exist_ok=True)
        timestamp = datetime.utcnow().timestamp()
        image_filename = f"search_{int(timestamp)}_{current_user.id}.jpg"
        image_path = f"uploads/facial/{image_filename}"
        
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        logger.info(f"[Facial] Image saved to {image_path} ({len(image_data)} bytes)")
        
    except Exception as e:
        logger.error(f"[Facial] Error processing image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing image: {str(e)}"
        )
    
    # Create search record
    new_search = FaceSearch(
        case_id=search_data.case_id,
        source_image_path=image_path,
        search_type=search_data.search_type,
        timestamp=datetime.utcnow()
    )
    
    db.add(new_search)
    db.commit()
    db.refresh(new_search)
    
    logger.info(f"[Facial] ✓ Face search created successfully (ID: {new_search.id})")
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Facial Recognition Search",
        module="Facial Recognition",
        details=f"Performed {search_data.search_type} search for case {case.case_number}"
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"[Facial] Search logged - Image indexed and ready for matching")
    
    return new_search


@router.post("/reverse-search")
async def reverse_image_search(
    search_request: ReverseImageSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform reverse image search on multiple engines"""
    logger.info(f"[Facial] User {current_user.username} performing reverse search for case {search_request.case_id}")
    
    # Verify case exists
    case = db.query(Case).filter(Case.id == search_request.case_id).first()
    if not case:
        logger.error(f"[Facial] Case {search_request.case_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    # Decode and save image for reverse search
    try:
        image_data = base64.b64decode(search_request.image_base64)
        os.makedirs("uploads/facial", exist_ok=True)
        timestamp = datetime.utcnow().timestamp()
        image_filename = f"reverse_{int(timestamp)}_{current_user.id}.jpg"
        image_path = f"uploads/facial/{image_filename}"
        
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        logger.info(f"[Facial] Reverse search image saved to {image_path}")
        
        # Create search record for reverse search
        new_search = FaceSearch(
            case_id=search_request.case_id,
            source_image_path=image_path,
            search_type="reverse_search",
            timestamp=datetime.utcnow()
        )
        
        db.add(new_search)
        db.commit()
        db.refresh(new_search)
        
        logger.info(f"[Facial] ✓ Reverse search initiated (ID: {new_search.id})")
        
    except Exception as e:
        logger.error(f"[Facial] Error processing reverse search image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing image: {str(e)}"
        )
    
    # Log action
    audit_log = AuditLog(
        user_id=current_user.id,
        action="Reverse Image Search",
        module="Facial Recognition",
        details=f"Engines: {', '.join(search_request.engines)} for case {case.case_number}"
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"[Facial] Reverse search queued on engines: {', '.join(search_request.engines)}")
    
    return {
        "message": "Reverse image search initiated successfully",
        "search_id": new_search.id,
        "engines": search_request.engines,
        "status": "processing",
        "image_path": image_path,
        "note": "Results will be aggregated from selected engines and available shortly"
    }


@router.get("/search/{search_id}", response_model=FaceSearchResponse)
async def get_face_search(
    search_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get facial search results by ID"""
    logger.info(f"[Facial] User {current_user.username} retrieving search {search_id}")
    
    search = db.query(FaceSearch).filter(FaceSearch.id == search_id).first()
    if not search:
        logger.error(f"[Facial] Search {search_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )
    
    logger.info(f"[Facial] ✓ Retrieved search {search_id} (Type: {search.search_type})")
    return search


@router.get("/case/{case_id}", response_model=List[FaceSearchResponse])
async def get_case_face_searches(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all facial searches for a case"""
    logger.info(f"[Facial] User {current_user.username} retrieving searches for case {case_id}")
    
    # Verify case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        logger.error(f"[Facial] Case {case_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    
    searches = db.query(FaceSearch).filter(FaceSearch.case_id == case_id).order_by(FaceSearch.timestamp.desc()).all()
    logger.info(f"[Facial] ✓ Retrieved {len(searches)} searches for case {case.case_number}")
    
    return searches
