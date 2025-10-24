"""Script to write whatsapp router content"""

content = '''"""
WhatsApp Profiler Router - Complete Implementation
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
from datetime import datetime
import io, logging, os

from backend.database.database import get_db
from backend.database.models import WhatsAppProfile, User, Case, AuditLog
from backend.schemas.whatsapp import WhatsAppProfileCreate, WhatsAppProfileResponse, WhatsAppBulkUpload, WhatsAppExportRequest
from backend.routers.auth import get_current_user
from backend.modules.whatsapp_scraper import get_scraper_instance, close_scraper_instance

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

@router.get("/qr-code")
async def get_qr_code(current_user: User = Depends(get_current_user)):
    logger.info(f"[WhatsApp] User {current_user.username} requested QR code")
    try:
        scraper = await get_scraper_instance()
        await scraper.initialize()
        is_logged_in = await scraper.check_session_active()
        if is_logged_in:
            return {"is_logged_in": True, "message": "Already logged in"}
        qr_code = await scraper.get_qr_code()
        return {"is_logged_in": False, "qr_code": qr_code, "message": "Scan QR code"}
    except Exception as e:
        logger.error(f"[WhatsApp] QR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wait-for-login")
async def wait_for_login(timeout: int = 300, current_user: User = Depends(get_current_user)):
    logger.info(f"[WhatsApp] Waiting for login")
    try:
        scraper = await get_scraper_instance()
        success = await scraper.wait_for_login(timeout=timeout)
        return {"success": success, "message": "Login successful" if success else "Timeout"}
    except Exception as e:
        logger.error(f"[WhatsApp] Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape", response_model=WhatsAppProfileResponse)
async def scrape_profile(request: WhatsAppProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"[WhatsApp] Scraping {request.phone_number}")
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        scraper = await get_scraper_instance()
        if not await scraper.check_session_active():
            raise HTTPException(status_code=401, detail="Not logged in")
        profile_data = await scraper.scrape_profile(request.phone_number)
        profile = WhatsAppProfile(phone_number=request.phone_number, display_name=profile_data.get("display_name"), about=profile_data.get("about"), profile_picture_path=profile_data.get("profile_picture"), last_seen=profile_data.get("last_seen"), is_available=profile_data.get("is_available", False), scraped_at=datetime.utcnow(), case_id=request.case_id)
        db.add(profile)
        db.add(AuditLog(user_id=current_user.id, action="whatsapp_scrape", details=f"Scraped {request.phone_number}", timestamp=datetime.utcnow()))
        db.commit()
        db.refresh(profile)
        return profile
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[WhatsApp] Scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape/bulk")
async def bulk_scrape(request: WhatsAppBulkUpload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"[WhatsApp] Bulk scraping {len(request.phone_numbers)} profiles")
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        scraper = await get_scraper_instance()
        if not await scraper.check_session_active():
            raise HTTPException(status_code=401, detail="Not logged in")
        results = await scraper.scrape_multiple(phone_numbers=request.phone_numbers, delay_between=(2,5))
        saved_count = 0
        profile_responses = []
        for phone, data in results.items():
            try:
                profile = WhatsAppProfile(phone_number=phone, display_name=data.get("display_name"), about=data.get("about"), profile_picture_path=data.get("profile_picture"), last_seen=data.get("last_seen"), is_available=data.get("is_available", False), scraped_at=datetime.utcnow(), case_id=request.case_id)
                db.add(profile)
                db.flush()
                saved_count += 1
                profile_responses.append(profile)
            except Exception as e:
                logger.error(f"[WhatsApp] Error saving {phone}: {e}")
        db.add(AuditLog(user_id=current_user.id, action="whatsapp_bulk", details=f"Scraped {saved_count} profiles", timestamp=datetime.utcnow()))
        db.commit()
        return {"total": len(request.phone_numbers), "saved": saved_count, "results": profile_responses}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[WhatsApp] Bulk error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...), case_id: int = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"[WhatsApp] Uploading CSV: {file.filename}")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Must be CSV")
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        phone_columns = ['phone_number', 'phone', 'number', 'Phone Number']
        phone_column = next((col for col in phone_columns if col in df.columns), None)
        if not phone_column:
            raise HTTPException(status_code=400, detail=f"Need phone_number column. Found: {df.columns.tolist()}")
        phone_numbers = df[phone_column].dropna().astype(str).unique().tolist()
        return {"message": "CSV parsed", "total_rows": len(df), "phone_numbers": phone_numbers, "count": len(phone_numbers)}
    except Exception as e:
        logger.error(f"[WhatsApp] CSV error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/case/{case_id}", response_model=List[WhatsAppProfileResponse])
async def get_case_profiles(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profiles = db.query(WhatsAppProfile).filter(WhatsAppProfile.case_id == case_id).order_by(WhatsAppProfile.scraped_at.desc()).all()
    return profiles

@router.post("/export")
async def export_profiles(request: WhatsAppExportRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"[WhatsApp] Exporting case {request.case_id}")
    profiles = db.query(WhatsAppProfile).filter(WhatsAppProfile.case_id == request.case_id).all()
    if not profiles:
        raise HTTPException(status_code=404, detail="No profiles")
    try:
        data = [{"Phone Number": p.phone_number, "Display Name": p.display_name or "N/A", "About": p.about or "N/A", "Last Seen": p.last_seen or "N/A", "Available": "Yes" if p.is_available else "No", "Scraped At": p.scraped_at.strftime("%Y-%m-%d %H:%M:%S")} for p in profiles]
        df = pd.DataFrame(data)
        os.makedirs("reports", exist_ok=True)
        filename = f"whatsapp_case_{request.case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join("reports", filename)
        df.to_excel(filepath, index=False, engine='openpyxl')
        db.add(AuditLog(user_id=current_user.id, action="whatsapp_export", details=f"Exported {len(profiles)} profiles", timestamp=datetime.utcnow()))
        db.commit()
        return {"message": "Export successful", "filename": filename, "profile_count": len(profiles), "download_url": f"/api/whatsapp/download/{filename}"}
    except Exception as e:
        logger.error(f"[WhatsApp] Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_export(filename: str, current_user: User = Depends(get_current_user)):
    filepath = os.path.join("reports", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=filename)

@router.post("/close-session")
async def close_session(current_user: User = Depends(get_current_user)):
    logger.info("[WhatsApp] Closing session")
    try:
        await close_scraper_instance()
        return {"success": True, "message": "Session closed"}
    except Exception as e:
        logger.error(f"[WhatsApp] Close error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
'''

with open('d:\\osint\\backend\\routers\\whatsapp.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ WhatsApp router written successfully")
