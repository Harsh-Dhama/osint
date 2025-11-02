"""
WhatsApp Profiler Router - Complete Implementation
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
from datetime import datetime
import io, logging, os, random, asyncio

from backend.database.database import get_db
from backend.database.models import WhatsAppProfile, User, Case, AuditLog
from backend.schemas.whatsapp import WhatsAppProfileCreate, WhatsAppProfileResponse, WhatsAppBulkUpload, WhatsAppExportRequest
from backend.routers.auth import get_current_user
from backend.modules.whatsapp_scraper import get_scraper_instance, close_scraper_instance
from backend.utils.pdf_generator import generate_whatsapp_profile_pdf, generate_whatsapp_bulk_pdf

logger = logging.getLogger(__name__)
router = APIRouter(tags=["whatsapp"])

@router.get("/qr-code")
async def get_qr_code(current_user: User = Depends(get_current_user)):
    logger.info(f"[WhatsApp] User {current_user.username} requested QR code")
    try:
        scraper = await get_scraper_instance()
        # Initialize in HEADFUL mode so user can see the real WhatsApp Web page
        # This shows the actual QR code that WhatsApp generates, avoiding any
        # extraction/modification issues that can make QR codes unscannable
        await scraper.initialize(headless=False)
        is_logged_in = await scraper.check_session_active()
        if is_logged_in:
            return {"is_logged_in": True, "message": "Already logged in", "browser_visible": True}
        
        # Navigate to WhatsApp Web and let the user scan directly from the browser window
        await scraper.show_whatsapp_web_for_login()
        
        return {
            "is_logged_in": False, 
            "message": "WhatsApp Web opened in browser window. Please scan the QR code displayed there.",
            "browser_visible": True,
            "instruction": "A browser window has opened with WhatsApp Web. Scan the QR code with your phone."
        }
    except Exception as e:
        error_msg = f"QR endpoint error: {type(e).__name__}: {str(e)}"
        logger.error(f"[WhatsApp] {error_msg}", exc_info=True)
        # Write to file for debugging
        try:
            import traceback
            with open("logs/qr_error.log", "w") as f:
                f.write(f"{error_msg}\n\n")
                f.write(traceback.format_exc())
        except:
            pass
        raise HTTPException(status_code=500, detail=error_msg)

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
    """
    FULLY AUTOMATED WhatsApp profile scraping.
    User provides only phone number, system navigates and extracts everything automatically.
    Perfect for frontend integration - no manual steps required.
    """
    logger.info(f"[WhatsApp] AUTO-SCRAPE: Starting for {request.phone_number}")
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        scraper = await get_scraper_instance()
        if not await scraper.check_session_active():
            raise HTTPException(status_code=401, detail="Not logged in to WhatsApp Web")
        
        # Use fully automated navigation and extraction
        profile_data = await scraper.auto_navigate_and_extract(request.phone_number)
        
        # Save to database
        profile = WhatsAppProfile(
            phone_number=request.phone_number,
            display_name=profile_data.get("display_name"),
            about=profile_data.get("about"),
            profile_picture_path=profile_data.get("profile_picture"),
            last_seen=profile_data.get("last_seen"),
            is_available=profile_data.get("is_available", False),
            scraped_at=datetime.utcnow(),
            case_id=request.case_id
        )
        db.add(profile)
        db.add(AuditLog(
            user_id=current_user.id,
            action="whatsapp_auto_scrape",
            module="whatsapp",  # Fixed: added missing module field
            details=f"Auto-scraped {request.phone_number} - Status: {profile_data.get('status')} - Method: {profile_data.get('method')}",
            timestamp=datetime.utcnow()
        ))
        db.commit()
        db.refresh(profile)
        
        logger.info(f"[WhatsApp] AUTO-SCRAPE: Completed for {request.phone_number} - Status: {profile_data.get('status')}")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[WhatsApp] AUTO-SCRAPE error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape/bulk")
async def bulk_scrape(request: WhatsAppBulkUpload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    FULLY AUTOMATED bulk scraping from CSV/Excel upload or manual number list.
    Perfect for frontend: user uploads file → system processes → reports generated.
    """
    logger.info(f"[WhatsApp] AUTO-BULK: Starting for {len(request.phone_numbers)} numbers")
    case = db.query(Case).filter(Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        scraper = await get_scraper_instance()
        if not await scraper.check_session_active():
            raise HTTPException(status_code=401, detail="Not logged in to WhatsApp Web")
        
        # Automated bulk processing
        results = {}
        saved_count = 0
        failed_count = 0
        profile_responses = []
        method_stats = {}
        
        for idx, phone in enumerate(request.phone_numbers, 1):
            logger.info(f"[WhatsApp] AUTO-BULK: Processing {idx}/{len(request.phone_numbers)}: {phone}")
            
            try:
                # Fully automated extraction
                data = await scraper.auto_navigate_and_extract(phone)
                results[phone] = data
                
                method = data.get("method", "unknown")
                method_stats[method] = method_stats.get(method, 0) + 1
                
                # Save to database
                profile = WhatsAppProfile(
                    phone_number=phone,
                    display_name=data.get("display_name"),
                    about=data.get("about"),
                    profile_picture_path=data.get("profile_picture"),
                    last_seen=data.get("last_seen"),
                    is_available=data.get("is_available", False),
                    scraped_at=datetime.utcnow(),
                    case_id=request.case_id
                )
                db.add(profile)
                db.flush()
                saved_count += 1
                profile_responses.append(profile)
                
            except Exception as e:
                logger.error(f"[WhatsApp] AUTO-BULK: Error processing {phone}: {e}")
                failed_count += 1
                results[phone] = {"error": str(e), "status": "failed"}
            
            # Rate limiting between requests (increased for reliability)
            if idx < len(request.phone_numbers):
                delay = random.uniform(5, 8)  # Increased from 3-6 to 5-8 seconds
                logger.debug(f"[WhatsApp] AUTO-BULK: Waiting {delay:.1f}s before next...")
                await asyncio.sleep(delay)
        
        db.add(AuditLog(
            user_id=current_user.id,
            action="whatsapp_auto_bulk",
            module="whatsapp",  # Fixed: added missing module field
            details=f"Auto-scraped {saved_count}/{len(request.phone_numbers)} profiles; Failed: {failed_count}; Methods: {method_stats}",
            timestamp=datetime.utcnow()
        ))
        db.commit()
        
        logger.info(f"[WhatsApp] AUTO-BULK: Completed - Saved: {saved_count}, Failed: {failed_count}")
        return {
            "total": len(request.phone_numbers),
            "saved": saved_count,
            "failed": failed_count,
            "method_stats": method_stats,
            "results": profile_responses
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[WhatsApp] AUTO-BULK error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...), case_id: int = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Upload CSV or Excel file containing phone numbers for bulk scraping.
    Automatically detects phone number column and extracts all valid numbers.
    Supports: .csv, .xlsx, .xls files
    """
    logger.info(f"[WhatsApp] Uploading file: {file.filename}")
    
    # Validate file format
    allowed_extensions = ['.csv', '.xlsx', '.xls']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file format. Supported formats: CSV, XLSX, XLS. Got: {file_ext}"
        )
    
    try:
        contents = await file.read()
        
        # Parse file based on extension
        if file_ext == '.csv':
            df = pd.read_csv(io.BytesIO(contents))
        else:  # .xlsx or .xls
            df = pd.read_excel(io.BytesIO(contents))
        
        logger.info(f"[WhatsApp] File parsed: {len(df)} rows, columns: {df.columns.tolist()}")
        
        # Try to find phone number column (case-insensitive)
        phone_columns = [
            'phone_number', 'phone', 'number', 'Phone Number', 
            'PHONE', 'mobile', 'Mobile', 'cell', 'contact',
            'Phone', 'Number', 'Contact', 'Mobile Number'
        ]
        
        phone_column = None
        for col in df.columns:
            if col in phone_columns or col.lower() in [pc.lower() for pc in phone_columns]:
                phone_column = col
                break
        
        if not phone_column:
            raise HTTPException(
                status_code=400, 
                detail=f"Phone number column not found. Expected one of: {phone_columns[:5]}. Found columns: {df.columns.tolist()}"
            )
        
        # Extract and clean phone numbers
        phone_numbers = df[phone_column].dropna().astype(str).tolist()
        
        # Clean phone numbers: remove spaces, dashes, parentheses
        cleaned_numbers = []
        for num in phone_numbers:
            # Remove common formatting characters
            cleaned = num.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            # Only keep if it has digits
            if any(c.isdigit() for c in cleaned):
                cleaned_numbers.append(cleaned)
        
        # Remove duplicates while preserving order
        unique_numbers = list(dict.fromkeys(cleaned_numbers))
        
        logger.info(f"[WhatsApp] Extracted {len(unique_numbers)} unique phone numbers from {len(df)} rows")
        
        return {
            "message": "File parsed successfully",
            "total_rows": len(df),
            "phone_numbers": unique_numbers,
            "count": len(unique_numbers),
            "filename": file.filename,
            "column_used": phone_column
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WhatsApp] File upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")

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
        db.add(AuditLog(
            user_id=current_user.id,
            action="whatsapp_export",
            module="whatsapp",  # Fixed: added missing module field
            details=f"Exported {len(profiles)} profiles",
            timestamp=datetime.utcnow()
        ))
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

@router.post("/profile/{profile_id}/export-pdf")
async def export_profile_pdf(
    profile_id: int, 
    officer_name: str = "John Doe",
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Generate a professional PDF report for a single WhatsApp profile.
    Matches the WAProfiler format shown in the reference images.
    """
    logger.info(f"[WhatsApp] Generating PDF for profile {profile_id}")
    
    # Get profile from database
    profile = db.query(WhatsAppProfile).filter(WhatsAppProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    try:
        # Convert profile to dict
        profile_data = {
            "phone_number": profile.phone_number,
            "display_name": profile.display_name,
            "about": profile.about,
            "profile_picture": profile.profile_picture_path,
            "profile_picture_path": profile.profile_picture_path,
            "last_seen": profile.last_seen,
            "is_available": profile.is_available,
            "scraped_at": profile.scraped_at.strftime("%Y-%m-%d %H:%M:%S") if profile.scraped_at else None,
            "status": "success",
            "method": "database_export"
        }
        
        # Generate PDF
        case_id = f"C-{profile.case_id}" if profile.case_id else "C-UNKNOWN"
        pdf_path = generate_whatsapp_profile_pdf(
            profile_data=profile_data,
            case_id=case_id,
            officer_name=officer_name
        )
        
        # Log audit
        db.add(AuditLog(
            user_id=current_user.id,
            action="whatsapp_pdf_export",
            module="whatsapp",
            details=f"Generated PDF report for profile {profile_id} ({profile.phone_number})",
            timestamp=datetime.utcnow()
        ))
        db.commit()
        
        # Get filename for response
        filename = os.path.basename(pdf_path)
        
        logger.info(f"[WhatsApp] PDF generated: {pdf_path}")
        return {
            "success": True,
            "message": "PDF report generated successfully",
            "filename": filename,
            "download_url": f"/api/whatsapp/download-pdf/{filename}"
        }
    except Exception as e:
        logger.error(f"[WhatsApp] PDF generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.get("/download-pdf/{filename}")
async def download_pdf(filename: str, current_user: User = Depends(get_current_user)):
    """Download a generated PDF report"""
    filepath = os.path.join("reports", "whatsapp", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(
        filepath, 
        media_type="application/pdf", 
        filename=filename
    )

@router.post("/case/{case_id}/export-pdf")
async def export_case_pdf(
    case_id: int,
    officer_name: str = "John Doe",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a bulk PDF report for all profiles in a case.
    Includes summary statistics and detailed table of all profiles.
    """
    logger.info(f"[WhatsApp] Generating bulk PDF for case {case_id}")
    
    # Get all profiles for this case
    profiles = db.query(WhatsAppProfile).filter(WhatsAppProfile.case_id == case_id).all()
    if not profiles:
        raise HTTPException(status_code=404, detail="No profiles found for this case")
    
    try:
        # Convert profiles to dict list
        profiles_data = []
        for profile in profiles:
            profiles_data.append({
                "phone_number": profile.phone_number,
                "display_name": profile.display_name,
                "about": profile.about,
                "profile_picture": profile.profile_picture_path,
                "profile_picture_path": profile.profile_picture_path,
                "last_seen": profile.last_seen,
                "is_available": profile.is_available,
                "scraped_at": profile.scraped_at.strftime("%Y-%m-%d %H:%M:%S") if profile.scraped_at else None,
            })
        
        # Generate bulk PDF
        case_code = f"C-{case_id}"
        pdf_path = generate_whatsapp_bulk_pdf(
            profiles=profiles_data,
            case_id=case_code,
            officer_name=officer_name
        )
        
        # Log audit
        db.add(AuditLog(
            user_id=current_user.id,
            action="whatsapp_bulk_pdf_export",
            module="whatsapp",
            details=f"Generated bulk PDF for case {case_id} with {len(profiles)} profiles",
            timestamp=datetime.utcnow()
        ))
        db.commit()
        
        filename = os.path.basename(pdf_path)
        
        logger.info(f"[WhatsApp] Bulk PDF generated: {pdf_path}")
        return {
            "success": True,
            "message": f"Bulk PDF report generated for {len(profiles)} profiles",
            "filename": filename,
            "profile_count": len(profiles),
            "download_url": f"/api/whatsapp/download-pdf/{filename}"
        }
    except Exception as e:
        logger.error(f"[WhatsApp] Bulk PDF generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
