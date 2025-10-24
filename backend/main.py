import sys
import asyncio

# On Windows, ensure the Proactor event loop is used so subprocesses can be
# created from asyncio (required by Playwright). Do this early before any
# asyncio-based libraries are imported/used.
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        # If setting the policy fails for any reason, continue and let
        # Playwright raise an informative error later.
        pass

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.database.database import init_db, get_db
from backend.database.models import User
from backend.auth.security import decode_access_token
from backend.routers import auth, users, cases, whatsapp, facial, social, monitoring, username, tracker, admin
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="OSINT Platform API",
    description="Unified Digital Investigation Tool for Law Enforcement",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Allow all origins for the Electron desktop app and local dev servers.
    # Electron uses file:// origins which are not easily enumerated, so allow '*'
    # in development. For production narrow this to trusted origins.
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Dependency to get current user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
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


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp Profiler"])
app.include_router(facial.router, prefix="/api/facial", tags=["Facial Recognition"])
app.include_router(social.router, prefix="/api/social", tags=["Social Media Scraper"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Social Media Monitoring"])
app.include_router(username.router, prefix="/api/username", tags=["Username Searcher"])
app.include_router(tracker.router, prefix="/api/tracker", tags=["Number/Email Tracker"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("OSINT Platform API started successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OSINT Platform API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info"
    )
