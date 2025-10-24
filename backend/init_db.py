"""
Initialize OSINT Platform

This script:
1. Creates database tables
2. Creates default admin user
3. Sets up necessary directories
"""

import sys
import os
import asyncio

# Ensure project root is on sys.path so "from backend..." imports work
# when running this file directly (python backend/init_db.py)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.database.database import init_db, SessionLocal
from backend.database.models import User, SystemConfig
from backend.auth.security import get_password_hash
from datetime import datetime


def create_directories():
    """Create necessary directories"""
    directories = [
        "data",
        "uploads/whatsapp/profiles",
        "uploads/facial",
        "uploads/social",
        "reports",
        "backups",
        "logs",
        "data/face_database"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def create_default_admin():
    """Create default admin user if not exists"""
    db = SessionLocal()
    
    try:
        # Check if admin exists (avoid loading User if enum mismatch in DB)
        from sqlalchemy import text
        result = db.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'")).scalar()
        
        if result == 0:
            # Use raw SQL to insert admin with proper enum name 'ADMIN'
            db.execute(text("""
                INSERT INTO users (username, email, full_name, hashed_password, role, credits, 
                                 is_active, disclaimer_accepted, disclaimer_accepted_at, 
                                 created_at, updated_at)
                VALUES (:username, :email, :full_name, :hashed_password, :role, :credits,
                       :is_active, :disclaimer_accepted, :disclaimer_accepted_at,
                       :created_at, :updated_at)
            """), {
                "username": "admin",
                "email": "admin@osint.local",
                "full_name": "System Administrator",
                "hashed_password": get_password_hash("admin123"),
                "role": "ADMIN",  # Use enum NAME, not value
                "credits": 10000,
                "is_active": 1,
                "disclaimer_accepted": 1,
                "disclaimer_accepted_at": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
            })
            db.commit()
            print("✓ Created default admin user")
            print("  Username: admin")
            print("  Password: admin123")
            print("  ⚠️  Please change the password after first login!")
        else:
            print("✓ Admin user already exists")
    
    except Exception as e:
        print(f"✗ Error creating admin user: {str(e)}")
        db.rollback()
    
    finally:
        db.close()


def create_default_config():
    """Create default system configuration"""
    db = SessionLocal()
    
    try:
        default_configs = {
            "app_name": "OSINT Platform",
            "app_version": "1.0.0",
            "data_retention_days": "90",
            "auto_delete_enabled": "false",
            "default_user_credits": "100",
            "scraping_delay_min": "2",
            "scraping_delay_max": "5",
            "face_recognition_tolerance": "0.6",
            "agency_name": "Law Enforcement Agency",
            "confidentiality_watermark": "CONFIDENTIAL - FOR OFFICIAL USE ONLY"
        }
        
        for key, value in default_configs.items():
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not config:
                config = SystemConfig(key=key, value=value)
                db.add(config)
        
        db.commit()
        print("✓ Created default system configuration")
    
    except Exception as e:
        print(f"✗ Error creating config: {str(e)}")
        db.rollback()
    
    finally:
        db.close()


def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists(".env"):
        import shutil
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✓ Created .env file from .env.example")
            print("  ⚠️  Please update .env with your configuration!")
        else:
            print("⚠️  .env.example not found, please create .env manually")
    else:
        print("✓ .env file already exists")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("OSINT Platform - Initialization")
    print("=" * 60)
    print()
    
    # Create directories
    print("Creating directories...")
    create_directories()
    print()
    
    # Create .env file
    print("Setting up environment...")
    create_env_file()
    print()
    
    # Initialize database
    print("Initializing database...")
    init_db()
    print("✓ Database initialized")
    print()
    
    # Create admin user
    print("Creating default admin user...")
    create_default_admin()
    print()
    
    # Create default config
    print("Creating system configuration...")
    create_default_config()
    print()
    
    print("=" * 60)
    print("✅ Initialization completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update .env file with your configuration")
    print("2. Change admin password after first login")
    print("3. Install Playwright browsers: playwright install")
    print("4. Start the backend: python backend/main.py")
    print("5. Start the frontend: cd electron-app && npm start")
    print()


if __name__ == "__main__":
    main()
