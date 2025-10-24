
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from backend.database.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
# If sqlcipher3 is unavailable on the system (requires MSVC build tools), default to sqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/osint.db")

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Create engine
try:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
        poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    )
except Exception:
    # Fallback: if sqlcipher3 is referenced but not installed, switch to default sqlite file
    if "sqlcipher" in DATABASE_URL or "sqlcipher3" in DATABASE_URL:
        fallback_url = "sqlite:///./data/osint.db"
        engine = create_engine(
            fallback_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_db():
    """Reset database (drop all tables and recreate)"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset successfully")
